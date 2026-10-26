"""Mixins de restriction par role (Ch4 : autorisation au-dela de la connexion)."""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige un ou plusieurs roles SkillForge. Ex : allowed_roles = ['mentor']."""

    allowed_roles: list[str] = []

    def test_func(self):
        user = self.request.user
        if user.is_superuser or getattr(user, "role", None) == "admin":
            return True
        return getattr(user, "role", None) in self.allowed_roles
