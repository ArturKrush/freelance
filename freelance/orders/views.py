from django.shortcuts import render, redirect, get_object_or_404, reverse
from .forms import OrderTbForm, CompleteOrderTbForm, ProgressTbForm, OrderFilterForm
from django.views.generic import DetailView, ListView, UpdateView, DeleteView
from main.models import UserTb, PerformanceOfferTb, OrderTb, ProgressTb, RefersTb, SpecBranchTb
from django.db.models import Prefetch
from django.db import connection, DatabaseError
from django.contrib import messages
from main.views import dictfetchall, to_none_if_empty


class OrderDetailView(DetailView):
    model = OrderTb
    template_name = 'orders/details_view.html'
    context_object_name = 'order'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Отримуємо замовлення, яке вже є в self.object
        order = self.object

        # username = self.request.session.get('authenticated_user')
        # user = get_object_or_404(UserTb, username=username)

        # Шукаємо прийняту пропозицію для цього замовлення
        offer = PerformanceOfferTb.objects.filter(
            order=order,
            offer_status='Прийнято',
            # order__client=user
        ).select_related('performer').first()

        # Додаємо ім’я виконавця до контексту
        context['performer_username'] = offer.performer.username if offer else None
        return context


def orders_home(request):
    username = request.session.get('authenticated_user')

    if not username:
        return redirect('login')

    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        return redirect('login')

    orders = OrderTb.objects.filter(client=user).prefetch_related(
        Prefetch('refers', queryset=RefersTb.objects.select_related('spec_branch'))
    ).order_by('id')

    return render(request, 'orders/orders_home.html', {'orders': orders})


def create_order(request):
    if request.method == 'POST':
        form = OrderTbForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            username = request.session.get('authenticated_user')
            user = UserTb.objects.get(username=username)
            order.client = user
            order.save()

            form.save_m2m()

            return redirect('orders-home')
    else:
        form = OrderTbForm()

    return render(request, 'orders/create_order.html', {'form': form})


'''
class OrderProgressRedirectView(RedirectView):
    permanent = False  # тимчасове перенаправлення

    def get_redirect_url(self, *args, **kwargs):
        order_id = kwargs.get('order_id')
        # Можна додати перевірку, чи існує замовлення
        order = get_object_or_404(OrderTb, id=order_id)

        # Формуємо URL для списку прогресу цього замовлення
        return f'{order_id}/progress/'
'''


class OrderProgressListView(ListView):
    model = ProgressTb
    template_name = 'orders/order_progress.html'
    context_object_name = 'progress_list'

    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        username = self.request.session.get('authenticated_user')
        user = get_object_or_404(UserTb, username=username)

        # Перевіряємо, що замовлення належить цьому користувачу
        order = get_object_or_404(OrderTb, id=order_id, client_id=user.id)

        return ProgressTb.objects.filter(order_id=order.id).order_by('-creation_time')


class OrderUpdateView(UpdateView):
    model = OrderTb
    template_name = 'orders/create_order.html'

    form_class = OrderTbForm


def complete_order_form(request, order_id):
    order = get_object_or_404(OrderTb, id=order_id)

    if request.method == 'POST':
        form = CompleteOrderTbForm(request.POST)
        if form.is_valid():
            performance_grade_raw = form.cleaned_data.get('performance_grade')
            final_review_raw = form.cleaned_data.get('final_review')
            order_status = form.cleaned_data.get('order_status')

            performance_grade = (
                int(performance_grade_raw) if performance_grade_raw not in (None, "") else None
            )
            final_review = (
                final_review_raw if final_review_raw not in (None, "") else None
            )

            # Перевірка забороненої ситуації
            if order.order_status == OrderTb.OrderState.WAITING and (performance_grade is not None or final_review):
                messages.error(
                    request,
                    "Ви не можете оцінити виконавця, який не зробив жодного запису про прогрес. "
                    "Якщо Ви не задоволені спілкуванням з ним, то подайте скаргу."
                )
                return render(request, 'orders/complete_order.html', {
                    'form': form, 'order': order
                })

            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT complete_order(%s, %s, %s, %s);",
                        [order.id, order_status, performance_grade, final_review]
                    )
                messages.success(request, "Замовлення успішно завершено.")
                return redirect('orders-home')

            except Exception as e:
                messages.error(request, f"Помилка: {str(e)}")
    else:
        form = CompleteOrderTbForm()

    return render(request, 'orders/complete_order.html', {
        'form': form, 'order': order
    })


class OrderDeleteView(DeleteView):
    model = OrderTb
    template_name = 'orders/delete_order.html'

    success_url = '/orders'


def perf_orders(request):
    username = request.session.get('authenticated_user')

    if not username:
        return redirect('pg_login')

    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        return redirect('pg_login')

    # Перевіряємо, чи користувач має роль 'Виконавець'
    if user.role != UserTb.UserRole.PERFORMER:
        return redirect('pg_login')  # або вивести повідомлення / 403

    # Отримуємо замовлення, які виконує виконавець
    orders = OrderTb.objects.filter(
        performanceoffertb__performer=user
    ).exclude(
        order_status=OrderTb.OrderState.NEW
    ).prefetch_related(
        Prefetch(
            'refers',
            queryset=RefersTb.objects.select_related('spec_branch')
        )
    ).distinct().order_by('-creation_time')

    return render(request, 'orders/perf_orders.html', {
        'orders': orders,
        'user': user,
    })


def perf_progress(request, order_id, progress_id=None):
    order = get_object_or_404(OrderTb, id=order_id)
    progress_list = ProgressTb.objects.filter(order_id=order.id).order_by('-creation_time')

    if progress_id:
        progress_instance = get_object_or_404(ProgressTb, id=progress_id, order_id=order.id)
    else:
        progress_instance = None

    if request.method == 'POST':
        form = ProgressTbForm(request.POST, instance=progress_instance)
        if form.is_valid():
            progress = form.save(commit=False)
            if order.order_status in [OrderTb.OrderState.WAITING, OrderTb.OrderState.IN_PROGRESS]:
                progress.order = order
                progress.save()
                if progress_instance:
                    messages.success(request, "Запис про прогрес успішно оновлено.")
                else:
                    messages.success(request, "Запис про прогрес успішно додано.")
            else:
                messages.error(request, "Не можна додавати або змінювати прогрес виконаного замовлення.")
            return redirect('perf-progress', order_id=order.id)
    else:
        form = ProgressTbForm(instance=progress_instance)

    return render(request, 'orders/perf_progress.html', {
        'order': order,
        'progress_list': progress_list,
        'form': form,
        'editing': bool(progress_instance),
        'progress_instance': progress_instance,
    })


def orders_search(request):
    form = OrderFilterForm(request.GET or None)
    filters_applied = False
    orders = []

    if form.is_valid():
        specialty = form.cleaned_data.get('specialty')
        branches = form.cleaned_data.get('branch')
        name_query = request.GET.get('q', '').strip() or None

        specialty_name = specialty.specialty_name if specialty else None
        branch_names = [b.branch_name for b in branches] if branches else None

        with connection.cursor() as cursor:
            cursor.execute("""
                           SELECT *
                           FROM get_filtered_orders(%s, %s, %s)
                           """, [
                               specialty_name,
                               branch_names,
                               name_query,
                           ])
            result = dictfetchall(cursor)

        filters_applied = any([specialty_name, branch_names, name_query])
        orders = result
    else:
        # Якщо форма не валідна або GET порожній, показати всі замовлення без фільтрів
        with connection.cursor() as cursor:
            cursor.execute("""
                           SELECT *
                           FROM get_filtered_orders(NULL, NULL, NULL)
                           """)
            orders = dictfetchall(cursor)

    return render(request, 'orders/orders_search.html', {
        'orders': orders,
        'form': form,
        'filters_applied': filters_applied,
    })


class ProgressDeleteView(DeleteView):
    model = ProgressTb
    template_name = 'orders/delete_progress.html'

    def get_success_url(self):
        return reverse('perf-progress', kwargs={'performer_id': self.object.performer_id})