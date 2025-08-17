from django.shortcuts import render, redirect
from main.models import UserTb, OrderTb, PerformanceOfferTb
from django.db.models import Avg, Subquery, OuterRef, F
from django.db import connection, DatabaseError
from django.contrib import messages
from django.views.decorators.http import require_POST
from .forms import PerformanceOfferTbForm
from django.shortcuts import get_object_or_404
from django.http.response import HttpResponseForbidden
from django.views.generic import DetailView, ListView, UpdateView, DeleteView

import logging
logger = logging.getLogger(__name__)

def offers_home(request):
    username = request.session.get('authenticated_user')
    user = UserTb.objects.get(username=username)

    # Отримаємо всі проєкти поточного користувача
    user_orders = OrderTb.objects.filter(client=user)
    offers = PerformanceOfferTb.objects.filter(order__in=user_orders).annotate(
        avg_grade=Subquery(
            OrderTb.objects.filter(
                performanceoffertb__performer=OuterRef('performer'),
                performance_grade__isnull=False
            )
            .values('performanceoffertb__performer')  # групування по виконавцю
            .annotate(avg=Avg('performance_grade'))
            .values('avg')[:1]
        ),
        order_topic=F('order__topic')
    )

    return render(request, 'offers/offers_home.html', {'offers': offers})


@require_POST
def accept_offer(request):
    offer_id = request.POST.get("offer_id")
    # next_url = request.POST.get("next") or request.META.get("HTTP_REFERER", "/")

    if not offer_id:
        messages.error(request, "Ідентифікатор пропозиції не передано.")
        return redirect("offers-home")  # або інша твоя сторінка

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


def reject_offer(request):
    offer_id = request.POST.get("offer_id")

    if not offer_id:
        messages.error(request, "Ідентифікатор пропозиції не передано.")
        return redirect("offers-home")

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT reject_offer(%s);", [offer_id])
            # messages.success(request, "Пропозицію прийнято.")
    except Exception as e:
        err_msg = str(e)
        if hasattr(e, 'args') and len(e.args) > 0:
            err_msg = e.args[0]

        messages.error(request, f"Помилка: {err_msg}")

    return redirect(request.META.get("HTTP_REFERER", "offers-home"))


def performer_offers(request):
    username = request.session.get('authenticated_user')
    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        return redirect('pg_login')
    if user.role != UserTb.UserRole.PERFORMER:
        return redirect('pg_login')

    offers = PerformanceOfferTb.objects.filter(
        performer=user
    ).select_related('order').order_by('-creation_time')

    return render(request, 'offers/performer_offers.html', {'offers': offers})


def create_offer(request, order_id):
    order = get_object_or_404(OrderTb, id=order_id)

    if request.method == 'POST':
        form = PerformanceOfferTbForm(request.POST)
        if form.is_valid():
            performer_offer = form.save(commit=False)
            username = request.session.get('authenticated_user')
            user = UserTb.objects.get(username=username)

            performer_offer.order = order
            performer_offer.performer = user
            performer_offer.save()
            messages.success(request, "Пропозицію успішно подано.")
            return redirect('orders-search')
    else:
        form = PerformanceOfferTbForm()

    return render(request, 'offers/create_offer.html', {
        'form': form,
        'order': order
    })


def agree_break(request):
    if request.method == "POST":
        offer_id = request.POST.get("offer_id")
        offer = get_object_or_404(PerformanceOfferTb, id=offer_id)

        username = request.session.get("authenticated_user")
        performer = get_object_or_404(UserTb, username=username)

        if offer.performer != performer:
            return HttpResponseForbidden("У вас немає прав для цієї дії.")

        offer.is_breaking_agreed = True
        offer.save()
    return redirect("performer-offers")


def disagree_break(request):
    if request.method == "POST":
        offer_id = request.POST.get("offer_id")
        offer = get_object_or_404(PerformanceOfferTb, id=offer_id)

        username = request.session.get("authenticated_user")
        performer = get_object_or_404(UserTb, username=username)

        if offer.performer != performer:
            return HttpResponseForbidden("У вас немає прав для цієї дії.")

        offer.is_breaking_agreed = False
        offer.save()
    return redirect("performer-offers")


class OfferUpdateView(UpdateView):
    model = PerformanceOfferTb
    template_name = 'offers/create_offer.html'

    form_class = PerformanceOfferTbForm
    success_url = '/offers/performer/'


class OfferDeleteView(DeleteView):
    model = PerformanceOfferTb
    template_name = 'offers/delete_offer.html'

    success_url = '/offers/performer/'