from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, UpdateView
from main.models import UserTb, OrderTb, SpecBranchTb, PerformersBranchesTb, PortfolioBySuccessfullyPerformedOrders, \
    WarnedUsers
from django.db.models import Avg, Q, Prefetch, F, Count
from .forms import PgLoginForm, ChangeClientProfileTbForm, PerformerFilterForm, ClientSearchForm
# import psycopg2
from django.db import connection
# from django.conf import settings
from django.contrib import messages
from .utils import change_database_credentials, test_db_credentials
# from django.contrib.auth.decorators import login_required
from collections import defaultdict
from django.http import HttpResponseForbidden


def login_view(request):
    if request.method == 'POST':
        form = PgLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # 1. Перевірка підключення
            if not test_db_credentials(username, password):
                messages.error(request, "Невірні облікові дані.")
                return render(request, 'main/login.html', {'form': form})

            # 2. Зміна підключення для перевірки через ORM
            change_database_credentials(username, password)

            try:
                user = UserTb.objects.using('default').get(username=username)
            except UserTb.DoesNotExist:
                messages.error(request, "Користувача не знайдено.")
                return render(request, 'main/login.html', {'form': form})

            # 3. Перевірка на бан
            if user.is_banned:
                messages.error(request, "Ваш обліковий запис заблоковано.")
                return redirect('pg_login')  # <== ОБОВ’ЯЗКОВО return

            # 4. Сесія і нове підключення
            change_database_credentials(username, password)
            request.session['authenticated_user'] = username
            request.session['user_password'] = password

            # 5. Перенаправлення за роллю
            if user.role == UserTb.UserRole.CUSTOMER:
                return redirect('client-home')
            elif user.role == UserTb.UserRole.PERFORMER:
                return redirect('performer-home')
            elif user.role == UserTb.UserRole.ADMIN:
                return redirect('admin-home')
    else:
        form = PgLoginForm()

    return render(request, 'main/login.html', {'form': form})


class PerformersDetailView(DetailView):
    model = UserTb
    template_name = 'main/performers_view.html'
    context_object_name = 'performer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        username = self.request.session.get('authenticated_user')
        if not username:
            return redirect('pg_login')

        user = UserTb.objects.get(username=username)

        if user.role == UserTb.UserRole.CUSTOMER:
            context['base_template'] = 'main/layout.html'
        elif user.role == UserTb.UserRole.PERFORMER:
            context['base_template'] = 'main/performer_layout.html'
        elif user.role == UserTb.UserRole.ADMIN:
            context['base_template'] = 'main/admin_layout.html'
        else:
            context['base_template'] = 'main/layout.html'  # дефолт

        return context


def index(request):
    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')

    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        user = 'Користувача не знайдено'

    return render(request, 'main/index.html', {
        'title': 'Freelance',
        'user': user,
    })


def dictfetchall(cursor):
    "Returns all rows from a cursor as a list of dicts"
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def to_none_if_empty(val):
    return val if val not in ['', [], None] else None


def performers_search(request):
    form = PerformerFilterForm(request.GET or None)
    performers = []
    filters_applied = False

    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')
    user = UserTb.objects.get(username=username)

    if user.role == UserTb.UserRole.CUSTOMER:
        base_template = 'main/layout.html'
    elif user.role == UserTb.UserRole.PERFORMER:
        base_template = 'main/performer_layout.html'
    elif user.role == UserTb.UserRole.ADMIN:
        base_template = 'main/admin_layout.html'

    # logger.warning(f"request.GET: {request.GET}")

    if form.is_valid():
        specialty = form.cleaned_data.get('specialty')
        branches = form.cleaned_data.get('branch')
        min_cost = to_none_if_empty(form.cleaned_data.get('min_cost'))
        max_cost = to_none_if_empty(form.cleaned_data.get('max_cost'))
        availability_param = form.cleaned_data.get('availability')
        name_query = request.GET.get('q', '').strip() or None

        # Обробка інших параметрів
        specialty_id = specialty.id if specialty else None
        branch_ids = [b.id for b in branches] if branches else None
        availability = True if availability_param == "available" else None

        # logger.warning(f"Перед SQL: spec={specialty_id}, branches={branch_ids}, min={min_cost}, max={max_cost}, avail={availability}, q={name_query}")

        # Виклик SQL-функції
        with connection.cursor() as cursor:
            cursor.execute("""
                           SELECT *
                           FROM get_filtered_performers(%s, %s, %s, %s, %s, %s)
                           """, [
                               specialty_id,
                               branch_ids,
                               min_cost,
                               max_cost,
                               availability,
                               name_query,
                           ])
            result = dictfetchall(cursor)
            performer_ids = [row['id'] for row in result]

        filters_applied = any([
            specialty_id, branch_ids, min_cost is not None,
                                      max_cost is not None, availability is not None,
            name_query
        ])

        performers = UserTb.objects.filter(id__in=performer_ids)

    else:
        # Вивід усіх активних виконавців без фільтра
        performers = UserTb.objects.filter(
            role=UserTb.UserRole.PERFORMER,
            is_banned=False
        )

    # Підтягування пов'язаних напрямків і рейтингу
    performers = performers.prefetch_related(
        Prefetch('spec_branches', queryset=SpecBranchTb.objects.all())
    ).annotate(
        avg_rating=Avg(
            'performance_offer_set__order__performance_grade',
            filter=Q(performance_offer_set__order__order_status=OrderTb.OrderState.SUCCESS)
        )
    ).distinct().order_by(F('avg_rating').desc(nulls_last=True))

    return render(request, 'main/performers_search.html', {
        'performers': performers,
        'form': form,
        'filters_applied': filters_applied,
        'user': user,
        'base_template': base_template
    })


def get_curr_client(request, client_id=None):
    global perf_requested
    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')

    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        return redirect('pg_login')

    # Якщо користувач - клієнт, показуємо його власний профіль
    if user.role == UserTb.UserRole.CUSTOMER:
        client = user
        perf_requested = False
    else:
        # Якщо користувач не клієнт, перевіряємо параметр client_id
        if client_id is None:
            perf_requested = False
            return redirect('pg_login')
        try:
            client = UserTb.objects.get(id=client_id, role=UserTb.UserRole.CUSTOMER)
            perf_requested = True
        except UserTb.DoesNotExist:
            return render('pg_login')

        # Підрахунок успішно виконаних замовлень клієнта
    successful_orders_count = OrderTb.objects.filter(
        client=client,
        order_status='Виконане успішно'
    ).count()

    return render(request, 'main/client_profile.html', {
        'user': client,
        'perf_requested': perf_requested,
        'successful_orders_count': successful_orders_count
    })


def get_curr_performer(request, perform_id=None):
    global client_requested
    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')

    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        return redirect('pg_login')

    if user.role == UserTb.UserRole.PERFORMER:
        performer = user
        client_requested = False
    else:
        if perform_id is None:
            client_requested = False
            return redirect('pg_login')
        try:
            performer = UserTb.objects.get(id=perform_id, role=UserTb.UserRole.PERFORMER)
            client_requested = True
        except UserTb.DoesNotExist:
            return render('pg_login')

    avg_grade_result = OrderTb.objects.filter(
        performanceoffertb__performer=performer,
        order_status='Виконане успішно',
        performanceoffertb__offer_status='Прийнято',
    ).aggregate(avg_grade=Avg('performance_grade'))
    avg_grade = avg_grade_result['avg_grade']

    # Отримання напрямків виконавця
    branches = SpecBranchTb.objects.filter(
        performersbranchestb__performer=performer
    ).distinct()

    return render(request, 'main/performer_profile.html', {
        'performer': performer,
        'client_requested': client_requested,
        'avg_grade': avg_grade,
        'branches': branches
    })


class ProfileUpdateView(UpdateView):
    model = UserTb
    template_name = 'main/update_profile.html'
    form_class = ChangeClientProfileTbForm
    success_url = '/users/client_profile'

    def get_object(self, queryset=None):
        username = self.request.session.get('authenticated_user')
        if not username:
            return redirect('pg_login')
        return UserTb.objects.get(username=username)


def fetch_raw_query(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def ratings_view(request):
    performer_rating_query = """
                             SELECT s.specialty_name,
                                    u.username,
                                    u.email,
                                    c.city_name,
                                    u.initial_cost,
                                    u.is_available_for_orders,
                                    COUNT(DISTINCT o.id) AS successful_orders_count,
                                    RANK()                  OVER (PARTITION BY s.specialty_name ORDER BY COUNT(DISTINCT o.id) DESC) AS rank
                             FROM user_tb u
                                      JOIN static_cities_tb c ON u.city = c.id
                                      JOIN performers_branches_tb pb ON pb.performer_id = u.id
                                      JOIN spec_branch_tb sb ON sb.id = pb.spec_branch_id
                                      JOIN specialty_tb s ON s.id = sb.specialty_id
                                      JOIN performance_offer_tb po ON po.performer_id = u.id
                                      JOIN order_tb o ON o.id = po.order_id
                             WHERE u.role = 'Виконавець'
                               AND u.is_banned = FALSE
                               AND o.order_status = 'Виконане успішно'
                               AND po.offer_status = 'Прийнято'
                             GROUP BY s.specialty_name, u.username, u.email, c.city_name, u.initial_cost,
                                      u.is_available_for_orders \
                             """

    branch_completed_query = """
                             SELECT sb.branch_name,
                                    COUNT(DISTINCT o.id) AS completed_orders_count
                             FROM order_tb o
                                      JOIN refers_tb r ON r.order_id = o.id
                                      JOIN spec_branch_tb sb ON sb.id = r.spec_branch_id
                             WHERE o.order_status = 'Виконане успішно'
                             GROUP BY sb.branch_name
                             ORDER BY completed_orders_count DESC \
                             """

    branch_active_query = """
                          SELECT sb.branch_name,
                                 COUNT(DISTINCT o.id) AS active_orders_count
                          FROM order_tb o
                                   JOIN refers_tb r ON r.order_id = o.id
                                   JOIN spec_branch_tb sb ON sb.id = r.spec_branch_id
                          WHERE o.order_status IN (
                                                   'Нове',
                                                   'Очікує початку роботи',
                                                   'У роботі',
                                                   'Очікує нової пропозиції'
                              )
                          GROUP BY sb.branch_name
                          ORDER BY active_orders_count DESC \
                          """

    performers = fetch_raw_query(performer_rating_query)

    # Групуємо по specialty_name
    grouped_performers = defaultdict(list)
    for p in performers:
        grouped_performers[p["specialty_name"]].append(p)

    username = request.session.get('authenticated_user')
    user = UserTb.objects.get(username=username)
    # is_performer = False
    if user.role == UserTb.UserRole.CUSTOMER:
        base_template = 'main/layout.html'
    elif user.role == UserTb.UserRole.PERFORMER:
        base_template = 'main/performer_layout.html'
    elif user.role == UserTb.UserRole.ADMIN:
        base_template = 'main/admin_layout.html'
    # is_performer = True

    context = {
        'performer_ratings': dict(grouped_performers),
        'completed_branches': fetch_raw_query(branch_completed_query),
        'active_branches': fetch_raw_query(branch_active_query),
        'base_template': base_template,
        'user': user
    }

    return render(request, 'main/client_performer_rating.html', context)


def performer_index(request):
    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')

    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        user = 'Користувача не знайдено'

    return render(request, 'main/performer_index.html', {
        'title': 'Freelance',
        'user': user,
    })


def admin_index(request):
    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')

    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        user = 'Користувача не знайдено'

    return render(request, 'main/admin_index.html', {
        'title': 'Freelance',
        'user': user,
    })


def warned_users(request):
    table = WarnedUsers.objects.all().order_by('-accepted_complaints_count')
    return render(request, 'main/warned_users.html', {
        'table': table
    })


def performers_admin_view(request):
    form = PerformerFilterForm(request.GET or None)
    performers = []
    filters_applied = False

    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')
    user = UserTb.objects.get(username=username)

    if form.is_valid():
        specialty = form.cleaned_data.get('specialty')
        branches = form.cleaned_data.get('branch')
        min_cost = to_none_if_empty(form.cleaned_data.get('min_cost'))
        max_cost = to_none_if_empty(form.cleaned_data.get('max_cost'))
        availability_param = form.cleaned_data.get('availability')
        name_query = request.GET.get('q', '').strip() or None

        # Обробка інших параметрів
        specialty_id = specialty.id if specialty else None
        branch_ids = [b.id for b in branches] if branches else None
        availability = True if availability_param == "available" else None

        # Виклик SQL-функції
        with connection.cursor() as cursor:
            cursor.execute("""
                           SELECT *
                           FROM get_filtered_performers(%s, %s, %s, %s, %s, %s)
                           """, [
                               specialty_id,
                               branch_ids,
                               min_cost,
                               max_cost,
                               availability,
                               name_query,
                           ])
            result = dictfetchall(cursor)
            performer_ids = [row['id'] for row in result]

        performers = UserTb.objects.filter(id__in=performer_ids)

    else:
        # Вивід усіх активних виконавців без фільтра
        performers = UserTb.objects.filter(
            role=UserTb.UserRole.PERFORMER
        )

    # Підтягування пов'язаних напрямків і рейтингу
    performers = performers.prefetch_related(
        Prefetch('spec_branches', queryset=SpecBranchTb.objects.all())
    ).annotate(
        avg_rating=Avg(
            'performance_offer_set__order__performance_grade',
            filter=Q(performance_offer_set__order__order_status=OrderTb.OrderState.SUCCESS)
        )
    ).distinct().order_by(
    F('is_banned').asc(),  # незаблоковані вгору
    F('avg_rating').desc(nulls_last=True)  # всередині — за рейтингом
)

    return render(request, 'main/performers_admin_view.html', {
        'performers': performers,
        'form': form,
        'user': user
    })


def ban_user(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user = get_object_or_404(UserTb, id=user_id)

        username = request.session.get("authenticated_user")
        curr_user = get_object_or_404(UserTb, username=username)

        if curr_user.role != UserTb.UserRole.ADMIN:
            return HttpResponseForbidden("У вас немає прав для цієї дії.")

        user.is_banned = True
        user.save()

        if user.role == UserTb.UserRole.CUSTOMER:
            return redirect("clients-search")
    return redirect("performers-admin-view")


def unban_user(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user = get_object_or_404(UserTb, id=user_id)

        username = request.session.get("authenticated_user")
        curr_user = get_object_or_404(UserTb, username=username)

        if curr_user.role != UserTb.UserRole.ADMIN:
            return HttpResponseForbidden("У вас немає прав для цієї дії.")

        user.is_banned = False
        user.save()

        if user.role == UserTb.UserRole.CUSTOMER:
            return redirect("clients-search")
    return redirect("performers-admin-view")


def clients_search(request):
    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')

    form = ClientSearchForm(request.GET or None)
    name_query = request.GET.get('q', '').strip()

    clients = UserTb.objects.filter(role=UserTb.UserRole.CUSTOMER)

    if name_query:
        clients = clients.filter(username__icontains=name_query)

    clients = clients.annotate(
        successful_orders_count=Count(
            'ordertb',
            filter=Q(ordertb__order_status='Виконане успішно')
        )
    ).select_related('city')

    return render(request, 'main/client_search.html', {
        'clients': clients,
        'form': form
    })


def admin_profile(request):
    username = request.session.get('authenticated_user')
    if not username:
        return redirect('pg_login')

    try:
        user = UserTb.objects.get(username=username)
    except UserTb.DoesNotExist:
        return redirect('pg_login')

    if user.role == UserTb.UserRole.ADMIN:
        admin = user
    else:
        admin = UserTb.objects.get(role=UserTb.UserRole.ADMIN)

    return render(request, 'main/admin_profile.html', {
        'admin': admin,
        'user': user
    })


class AdminProfileUpdateView(UpdateView):
    model = UserTb
    template_name = 'main/update_profile.html'
    form_class = ChangeClientProfileTbForm
    success_url = '/users/admin_profile/'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('authenticated_user'):
            return redirect('pg_login')
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        username = self.request.session.get('authenticated_user')
        return get_object_or_404(UserTb, username=username)