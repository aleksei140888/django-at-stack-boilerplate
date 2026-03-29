from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Email is required"))
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True"))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True"))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        GUEST = "guest", _("Guest")
        USER = "user", _("User")
        MODERATOR = "moderator", _("Moderator")
        ADMIN = "admin", _("Admin")

    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=150, blank=True)
    last_name = models.CharField(_("last name"), max_length=150, blank=True)
    role = models.CharField(
        _("role"),
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    avatar = models.ImageField(_("avatar"), upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(_("bio"), blank=True)

    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)

    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    last_seen = models.DateTimeField(_("last seen"), null=True, blank=True)

    # GDPR
    gdpr_consent = models.BooleanField(_("GDPR consent"), default=False)
    gdpr_consent_date = models.DateTimeField(_("GDPR consent date"), null=True, blank=True)

    # Email notifications
    email_notifications = models.BooleanField(_("email notifications"), default=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_moderator(self):
        return self.role in (self.Role.MODERATOR, self.Role.ADMIN) or self.is_staff

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        return self.first_name or self.email.split("@")[0]
