from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.utils import timezone
from main.models import ReviewTb, UserTb, ComplaintTb, PortfolioTb
from django.views.generic import DetailView, ListView, DeleteView, UpdateView
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods
from django.db import connection, IntegrityError, DatabaseError
from .forms import ReviewTbForm, AddComplaintForm, AddPortfolioForm
from django.http import HttpResponseForbidden

'''
@require_POST
def reviews_home(request):
    offer_id = request.POST.get("offer_id")

    if not offer_id:
        messages.error(request, "Ідентифікатор пропозиції не передано.")
        return redirect("performers-detail")  # або інша твоя сторінка

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT accept_offer(%s);", [offer_id])
        # messages.success(request, "Пропозицію прийнято.")
    except Exception as e:
        err_msg = str(e)
        if hasattr(e, 'args') and len(e.args) > 0:
            err_msg = e.args[0]  # Це найчастіше і є повідомлення з RAISE EXCEPTION

        messages.error(request, f"Помилка: {err_msg}")

    return redirect(request.META.get("HTTP_REFERER", "offers-home"))
'''

class PerformersReviewsListView(ListView):
    model = ReviewTb
    template_name = 'disputes/performers_reviews.html'
    context_object_name = 'reviews_list'

    def dispatch(self, request, *args, **kwargs):
        username = request.session.get('authenticated_user')
        if not username:
            return redirect('pg_login')
        try:
            self.user = UserTb.objects.get(username=username)
        except UserTb.DoesNotExist:
            return redirect('pg_login')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        performer_id = self.kwargs.get('performer_id')
        return ReviewTb.objects.filter(commented_person=performer_id).order_by('-creation_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['form'] = ReviewTbForm()
        context['performer_id'] = self.kwargs.get('performer_id')
        context['current_user'] = self.user

        role_template_map = {
            UserTb.UserRole.CUSTOMER: 'main/layout.html',
            UserTb.UserRole.PERFORMER: 'main/performer_layout.html',
            UserTb.UserRole.ADMIN: 'main/admin_layout.html',
        }

        role = getattr(self.user, 'role', None)
        context['base_template'] = role_template_map.get(role, 'main/layout.html')

        return context


class PerformersPortfolioListView(ListView):
    template_name = 'disputes/performers_portfolio.html'
    context_object_name = 'portfolio_list'

    def dispatch(self, request, *args, **kwargs):
        username = request.session.get('authenticated_user')
        if not username:
            return redirect('pg_login')
        self.user = UserTb.objects.get(username=username)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        performer_id = self.kwargs.get('performer_id')
        if performer_id is None:
            return []

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM get_performer_portfolio(%s)", [performer_id])
            result = cursor.fetchall()
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        role_template_map = {
            UserTb.UserRole.CUSTOMER: 'main/layout.html',
            UserTb.UserRole.PERFORMER: 'main/performer_layout.html',
            UserTb.UserRole.ADMIN: 'main/admin_layout.html',
        }

        context['base_template'] = role_template_map.get(
            getattr(self, 'user', None) and self.user.role,
            'main/layout.html'
        )

        return context


@require_POST
def create_review(request, performer_id):
    form = ReviewTbForm(request.POST)
    if form.is_valid():
        review_text = form.cleaned_data['review_text']

        try:
            username = request.session.get('authenticated_user')
            user = UserTb.objects.get(username=username)

            with connection.cursor() as cursor:
                cursor.execute("SELECT add_review(%s, %s, %s)", [user.id, performer_id, review_text])

            messages.success(request, "Відгук успішно додано.")
            return redirect('performers-reviews', performer_id=performer_id)

        except Exception as e:
            err_msg = str(e)
            if hasattr(e, 'args') and len(e.args) > 0:
                err_msg = e.args[0]

            messages.error(request, f"Помилка при додаванні відгуку: {err_msg}")

            # Повернення з формою та повідомленням
            reviews = ReviewTb.objects.filter(commented_person=performer_id).order_by('-creation_time')
            return render(request, 'disputes/performers_reviews.html', {
                'form': form,
                'reviews_list': reviews,
                'performer_id': performer_id
            })
    else:
        reviews = ReviewTb.objects.filter(commented_person=performer_id).order_by('-creation_time')
        return render(request, 'disputes/performers_reviews.html', {
            'form': form,
            'reviews_list': reviews,
            'performer_id': performer_id
        })


@require_http_methods(["GET", "POST"])
def user_complaints(request, user_id):
    offender = get_object_or_404(UserTb, id=user_id)

    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')
    complainant = get_object_or_404(UserTb, username=username)

    if request.method == 'POST':
        form = AddComplaintForm(request.POST, current_user=complainant) # делаю для исключения текущего пользователя из списка возможньіх нарушителей
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.complainant = complainant
            complaint.save()
            messages.success(request, "Скаргу успішно подано.")
            return redirect('user-complaints', user_id=user_id)
    else:
        form = AddComplaintForm(current_user=complainant)

    complaints = ComplaintTb.objects.filter(offender=user_id, is_accepted=True).order_by('-creation_time')
    return render(request, 'disputes/user_complaints.html', {
        'form': form,
        'complaints_list': complaints,
        'offender_id': offender.id
    })


def user_portfolio(request):
    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')

    user = get_object_or_404(UserTb, username=username)

    # Отримання портфоліо
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM get_performer_portfolio(%s)", [user.id])
        portfolio_list = cursor.fetchall()

    if request.method == 'POST':
        form = AddPortfolioForm(request.POST)
        if form.is_valid():
            description = form.cleaned_data['description']
            screenshot = form.cleaned_data['screenshot']
            try:
                # Виклик SQL-функції додавання
                with connection.cursor() as cursor:
                    cursor.execute("SELECT add_portfolio(%s, %s, %s)", [
                        user.id, description, screenshot
                    ])
                messages.success(request, "Ваше портфоліо успішно додане.")
                return redirect('user-portfolio')
            except IntegrityError as e:
                messages.error(request, "Цей запис вже існує у портфоліо.")
            except Exception as e:
                messages.error(request, f"Помилка при збереженні портфоліо: {str(e)}")
    else:
        form = AddPortfolioForm()

    return render(request, 'disputes/user_portfolio.html', {
        'form': form,
        'portfolio_list': portfolio_list
    })


def complaints_admin_view(request):
    complaints = ComplaintTb.objects.order_by('-creation_time')
    return render(request, 'disputes/complaints_for_admin.html', {
        'complaints_list': complaints
    })


def accept_complaint(request):
    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")
        complaint = get_object_or_404(ComplaintTb, id=complaint_id)

        username = request.session.get("authenticated_user")
        curr_user = get_object_or_404(UserTb, username=username)

        if curr_user.role != UserTb.UserRole.ADMIN:
            return HttpResponseForbidden("У вас немає прав для цієї дії.")

        complaint.is_accepted = True
        complaint.acceptance_time = timezone.now()
        complaint.save()
    return redirect("complaints-admin-view")


def reject_complaint(request):
    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")
        complaint = get_object_or_404(ComplaintTb, id=complaint_id)

        username = request.session.get("authenticated_user")
        curr_user = get_object_or_404(UserTb, username=username)

        if curr_user.role != UserTb.UserRole.ADMIN:
            return HttpResponseForbidden("У вас немає прав для цієї дії.")

        complaint.is_accepted = False
        complaint.save()
    return redirect("complaints-admin-view")


class PortfolioDeleteView(DeleteView):
    model = PortfolioTb
    template_name = 'disputes/delete_portfolio.html'

    def get_success_url(self):
        return reverse('user-portfolio')