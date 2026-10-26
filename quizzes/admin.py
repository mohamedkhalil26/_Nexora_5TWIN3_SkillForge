"""Admin quizzes — Ch3 : inlines questions/reponses + filtres seuils."""
from django.contrib import admin

from .models import Question, Quiz, Reponse, Tentative


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ("ordre", "type", "enonce", "points")
    show_change_link = True


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("titre", "cours", "nb_questions", "seuil_reussite", "actif", "cree_le")
    list_filter = ("actif", "cours__competence", "cree_le")
    search_fields = ("titre", "cours__titre")
    ordering = ("-cree_le",)
    inlines = [QuestionInline]

    @admin.display(description="Questions")
    def nb_questions(self, obj):
        return obj.questions.count()


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "quiz", "type", "points", "ordre")
    list_filter = ("type", "quiz")
    search_fields = ("enonce",)
    ordering = ("quiz", "ordre")


class ReponseInline(admin.TabularInline):
    model = Reponse
    extra = 0
    readonly_fields = ("question", "reponse_donnee", "correct", "points_obtenus")
    can_delete = False


@admin.register(Tentative)
class TentativeAdmin(admin.ModelAdmin):
    list_display = ("__str__", "quiz", "apprenant", "score", "reussi", "date")
    list_filter = ("reussi", "quiz", "date")
    search_fields = ("apprenant__username", "quiz__titre")
    ordering = ("-date",)
    readonly_fields = ("score", "reussi", "feedback")
    inlines = [ReponseInline]

    def has_add_permission(self, request):
        # Les tentatives naissent depuis l'app, pas depuis l'admin.
        return False
