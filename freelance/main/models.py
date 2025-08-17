# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django import forms

'''
class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'
'''

class ComplaintTb(models.Model):

    class ComplaintReason(models.TextChoices):
        NO_CONTACT_WITH_PERFORMER = 'Відсутність зв`язку з виконавцем'
        BAD_WORK_QUALITY = 'Робота не відповідає вимогам'
        DEADLINE_VIOLATION = 'Порушення термінів виконання'
        IP_VIOLATION = 'Порушення інтелект. власності'
        UNETHICAL_BEHAVIOR = 'Неетична поведінка'
        NO_CONTACT_WITH_CUSTOMER = 'Відсутність зв`язку з замовником'
        PAYMENT_ISSUES = 'Затримка або відмова в оплаті'
        REQUIREMENT_CHANGE = 'Необговорена зміна вимог'

    complainant = models.ForeignKey('UserTb', models.DO_NOTHING)
    offender = models.ForeignKey('UserTb', models.DO_NOTHING, related_name='complainttb_offender_set')
    description = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    reason = models.CharField(
        max_length=64,
        choices=ComplaintReason.choices
    )
    is_accepted = models.BooleanField(blank=True, null=True)
    acceptance_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'complaint_tb'


class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    receiver = models.ForeignKey('UserTb', models.DO_NOTHING, db_column='receiver')
    sender = models.ForeignKey('UserTb', models.DO_NOTHING, db_column='sender', related_name='message_sender_set')
    message_text = models.TextField()
    sending_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'message'


class OrderTb(models.Model):


    class OrderState(models.TextChoices):
        NEW = 'Нове', 'Нове'
        WAITING = 'Очікує початку роботи', 'Очікує початку роботи'
        IN_PROGRESS = 'У роботі', 'У роботі'
        WAITING_FOR_NEW = 'Очікує нової пропозиції', 'Очікує нової пропозиції'
        SUCCESS = 'Виконане успішно', 'Виконане успішно'
        FAIL = 'Виконане невдало', 'Виконане невдало'


    client = models.ForeignKey('UserTb', models.DO_NOTHING, db_column='client_id')
    topic = models.CharField(max_length=100)
    description = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    order_deadline = models.DateTimeField()
    start_of_work = models.DateTimeField(blank=True, null=True)
    performance_grade = models.SmallIntegerField(blank=True, null=True)
    final_review = models.TextField(blank=True, null=True)
    completion_time = models.DateTimeField(blank=True, null=True)
    order_status = models.CharField(
        # max_length=20,
        choices=OrderState.choices,
        default=OrderState.NEW,
        blank=True,
        null=False
    )

    update_time = models.DateTimeField(auto_now_add=True)

    spec_branches = models.ManyToManyField(
        'SpecBranchTb',
        through='RefersTb',
        related_name='orders'
    )


    class Meta:
        managed = False
        db_table = 'order_tb'


    def __str__(self):
        return self.topic


    def clean(self):
        super().clean()
        if self.order_deadline < timezone.now():
            raise ValidationError({'order_deadline': 'Deadline не може бути в минулому.'})

    def clean_performance_grade(self):
        grade = self.cleaned_data.get('performance_grade')
        if grade is not None and not (1 <= grade <= 10):
            raise forms.ValidationError('Оцінка повинна бути від 1 до 10.')
        return grade

    def get_absolute_url(self):
        return f'/orders/{self.id}'

class PerformanceOfferTb(models.Model):
    class OfferState(models.TextChoices):
        CONSIDERED = 'Розглядається', 'Розглядається'
        ACCEPTED = 'Прийнято', 'Прийнято'
        REJECTED = 'Відхилено', 'Відхилено'


    order = models.ForeignKey(OrderTb, models.DO_NOTHING)
    offer_status = models.CharField(
        # max_length=20,
        choices=OfferState.choices,
        default=OfferState.CONSIDERED,
        blank=True,
        null=False
    )
    creation_time = models.DateTimeField(auto_now_add=True)
    performer = models.ForeignKey('UserTb', models.DO_NOTHING, related_name='performance_offer_set')
    acceptance_time = models.DateTimeField(blank=True, null=True)
    offer_price = models.IntegerField()
    update_time = models.DateTimeField(auto_now_add=True)
    offer_text = models.TextField(blank=True, null=True)
    breaking_time = models.DateTimeField(blank=True, null=True)
    is_breaking_agreed = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'performance_offer_tb'
'''
    def get_absolute_url(self):
        return f'/offers/{self.id}'
'''

class PerformersBranchesTb(models.Model):
    pk = models.CompositePrimaryKey('performer_id', 'spec_branch_id')
    performer = models.ForeignKey('UserTb', models.CASCADE)
    spec_branch = models.ForeignKey('SpecBranchTb', models.CASCADE)

    class Meta:
        managed = False
        db_table = 'performers_branches_tb'
        unique_together = (('performer', 'spec_branch'),)


class PortfolioTb(models.Model):
    performer = models.ForeignKey('UserTb', models.DO_NOTHING)
    description = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    screenshot = models.CharField(max_length=255, blank=True, null=True)
    update_time = models.DateTimeField(blank=True, null=False, auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'portfolio_tb'


class ProgressTb(models.Model):
    order = models.ForeignKey(OrderTb, models.DO_NOTHING)
    text_info = models.TextField()
    screenshot = models.CharField(max_length=255, blank=True, null=True)
    creation_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'progress_tb'


class RefersTb(models.Model):
    pk = models.CompositePrimaryKey('order_id', 'spec_branch_id')
    spec_branch = models.ForeignKey('SpecBranchTb', models.DO_NOTHING, db_column='spec_branch_id')
    order = models.ForeignKey(OrderTb, models.DO_NOTHING, db_column="order_id", related_name='refers')

    class Meta:
        managed = False
        db_table = 'refers_tb'
        unique_together = (('order', 'spec_branch'),)


class ReviewTb(models.Model):
    commentator = models.ForeignKey('UserTb', models.DO_NOTHING)
    commented_person = models.ForeignKey('UserTb', models.DO_NOTHING, related_name='reviewtb_commented_person_set')
    review_text = models.TextField()
    creation_time = models.DateTimeField()
    update_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'review_tb'


class SpecBranchTb(models.Model):
    branch_name = models.CharField()
    specialty = models.ForeignKey('SpecialtyTb', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'spec_branch_tb'

    def __str__(self):
        return self.branch_name


class SpecialtyTb(models.Model):
    specialty_name = models.CharField()

    class Meta:
        managed = False
        db_table = 'specialty_tb'

    def __str__(self):
        return self.specialty_name


class StaticCitiesTb(models.Model):
    city_name = models.CharField(unique=True)


    def __str__(self):
        return self.city_name


    class Meta:
        managed = False
        db_table = 'static_cities_tb'


class UserTb(models.Model):


    class UserRole(models.TextChoices):
        CUSTOMER = 'Замовник', 'Замовник'
        PERFORMER = 'Виконавець', 'Виконавець'
        ADMIN = 'Адміністратор', 'Адміністратор'


    username = models.CharField(unique=True)
    role = models.CharField(
        # max_length=20,
        choices=UserRole.choices,
        default=UserRole.CUSTOMER
    )
    phone_num = models.CharField(max_length=13, blank=True, null=True)
    email = models.CharField(unique=True, max_length=35)
    account = models.CharField(max_length=29, blank=True, null=True)
    city = models.ForeignKey(StaticCitiesTb, models.DO_NOTHING, db_column='city', blank=True, null=True)
    initial_cost = models.PositiveIntegerField(blank=True, null=True)
    is_available_for_orders = models.BooleanField(blank=True, null=True)
    profile_text = models.TextField(blank=True, null=True)
    is_banned = models.BooleanField(blank=True, null=False, default=False)
    update_time = models.DateTimeField()


    spec_branches = models.ManyToManyField(
        'SpecBranchTb',
        through='PerformersBranchesTb',
        related_name='performers'
    )


    class Meta:
        managed = False
        db_table = 'user_tb'


    def __str__(self):
        return self.username

'''
    def get_absolute_url(self):
        return f'/users/client_profile/update/{self.id}/'
'''

class PortfolioBySuccessfullyPerformedOrders(models.Model):
    performer = models.ForeignKey('UserTb', models.DO_NOTHING)
    performer_username = models.CharField(unique=True)
    order = models.ForeignKey('OrderTb', models.DO_NOTHING)
    order_topic = models.CharField(max_length=100)
    order_description = models.TextField()
    completion_time = models.DateTimeField()
    last_screenshot = models.CharField(max_length=255)
    spec_branches = models.TextField()


    class Meta:
        managed = False  # 🔒 важливо! Django не має керувати представленням
        db_table = 'portfolio_by_successfully_performed_orders'


class WarnedUsers(models.Model):
    username = models.CharField(max_length=30, primary_key=True)
    role = models.CharField(
        choices=UserTb.UserRole.choices,
    )
    accepted_complaints_count = models.BigIntegerField()
    is_banned = models.BooleanField(blank=True, null=False)

    class Meta:
        managed = False  # 🔒 важливо! Django не має керувати представленням
        db_table = 'warned_users'