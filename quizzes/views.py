"""Vues quizzes — Mariem : CRUD mentor + passation apprenant avec correction IA."""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.mixins import RoleRequiredMixin

from certification.ai import detecter_similarite

from . import ai
from .forms import PasserQuizForm, QuestionForm, QuizForm
from .models import Question, Quiz, Reponse, Tentative


class QuizListView(ListView):
    paginate_by = 12
    model = Quiz
    template_name = "quizzes/quiz_list.html"
    context_object_name = "quiz_list"

    def get_queryset(self):
        return Quiz.objects.filter(actif=True).select_related("cours")


class QuizDetailView(DetailView):
    model = Quiz
    template_name = "quizzes/quiz_detail.html"
    context_object_name = "quiz"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            ctx["mes_tentatives"] = Tentative.objects.filter(
                quiz=self.object, apprenant=self.request.user
            )[:5]
            meilleur = (
                Tentative.objects.filter(quiz=self.object, apprenant=self.request.user)
                .order_by("-score")
                .first()
            )
            ctx["meilleur_score"] = meilleur.score if meilleur else None
        return ctx


class QuizCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["mentor"]
    model = Quiz
    form_class = QuizForm
    template_name = "quizzes/quiz_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class QuestionCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = ["mentor"]
    model = Question
    form_class = QuestionForm
    template_name = "quizzes/question_form.html"

    def get_success_url(self):
        return self.object.quiz.get_absolute_url()


class PasserQuizView(LoginRequiredMixin, View):
    """Passation : GET affiche, POST corrige (IA) et enregistre la tentative.

    Correctif roles n°3 : seuls les apprenants (ou le staff) peuvent passer
    un quiz, pour ne pas polluer les stats avec des tentatives mentor/admin.
    """

    template_name = "quizzes/passer_quiz.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not (
            getattr(user, "est_apprenant", False)
            or user.is_staff
            or getattr(user, "est_admin", False)
        ):
            messages.error(request, "Seuls les apprenants peuvent passer un quiz.")
            return redirect("quizzes:quiz-list")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, actif=True)
        form = PasserQuizForm(questions=quiz.questions.all())
        return render(request, self.template_name, {"quiz": quiz, "form": form})

    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk, actif=True)
        questions = list(quiz.questions.all())
        form = PasserQuizForm(request.POST, questions=questions)
        if not form.is_valid():
            return render(request, self.template_name, {"quiz": quiz, "form": form})

        tentative = Tentative.objects.create(quiz=quiz, apprenant=request.user)
        total_points = sum(q.points for q in questions) or 1
        points_obtenus = 0.0
        feedbacks = []
        for q in questions:
            donnee = form.cleaned_data.get(f"q_{q.pk}", "")
            # Point 10 : anti-fraude — copie d'une reponse d'un autre apprenant ?
            autres = list(
                Reponse.objects.filter(question=q)
                .exclude(tentative__apprenant=request.user)
                .values_list("reponse_donnee", flat=True)[:50]
            )
            if q.type == "qcm":
                ok, pts = ai.corriger_qcm(q, donnee)
                fb = ""
            else:
                ok, pts, fb = ai.corriger_libre(q, donnee)
                if fb:
                    feedbacks.append(f"Q{q.ordre} : {fb}")
            if detecter_similarite(str(donnee), autres):
                ok, pts = False, 0.0
                fb_suspect = f"Q{q.ordre} : réponse suspectée de copie, 0 point."
                feedbacks.append(fb_suspect)
            points_obtenus += pts
            Reponse.objects.create(
                tentative=tentative,
                question=q,
                reponse_donnee=str(donnee),
                correct=ok,
                points_obtenus=pts,
            )
        score = round(points_obtenus / total_points * 100, 1)
        tentative.score = score
        tentative.reussi = score >= quiz.seuil_reussite
        faibles = ", ".join(
            f"Q{r.question.ordre}" for r in tentative.reponses.filter(correct=False)
        )
        tentative.feedback = ai.feedback_quiz(tentative.reussi, score, faibles)
        if feedbacks:
            tentative.feedback += "\n\n" + "\n\n".join(feedbacks)
        tentative.save()
        messages.success(
            request,
            f"Quiz terminé : {score:.0f}% — {'réussi !' if tentative.reussi else 'à retravailler.'}",
        )
        return redirect("quizzes:tentative-detail", pk=tentative.pk)


class TentativeDetailView(LoginRequiredMixin, DetailView):
    model = Tentative
    template_name = "quizzes/tentative_detail.html"
    context_object_name = "tentative"

    def get_queryset(self):
        qs = Tentative.objects.select_related("quiz", "apprenant").prefetch_related(
            "reponses__question"
        )
        if self.request.user.is_staff:
            return qs
        return qs.filter(apprenant=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        t = self.object
        ctx["risque_ia"] = ai.predire_risque(
            list(
                Tentative.objects.filter(apprenant=t.apprenant).order_by("date").values_list(
                    "score", flat=True
                )
            )
        )
        return ctx


class MesTentativesView(LoginRequiredMixin, ListView):
    paginate_by = 10
    model = Tentative
    template_name = "quizzes/mes_tentatives.html"
    context_object_name = "tentatives"

    def get_queryset(self):
        return Tentative.objects.filter(apprenant=self.request.user).select_related("quiz")


class QuizUpdateView(RoleRequiredMixin, UpdateView):
    """CRUD Quiz : modification reservee aux mentors."""

    allowed_roles = ["mentor"]
    model = Quiz
    form_class = QuizForm
    template_name = "quizzes/quiz_form.html"

    def get_success_url(self):
        return self.object.get_absolute_url()


class QuizDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["mentor"]
    model = Quiz
    template_name = "quizzes/quiz_confirm_delete.html"
    success_url = reverse_lazy("quizzes:quiz-list")


class QuestionListView(LoginRequiredMixin, ListView):
    """Questions d'un quiz : visibles par tout connecte (passation a cote)."""

    template_name = "quizzes/question_list.html"
    context_object_name = "questions"

    def get_queryset(self):
        self.quiz = Quiz.objects.get(pk=self.kwargs["pk"])
        return self.quiz.questions.all()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["quiz"] = self.quiz
        return ctx


class QuestionUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ["mentor"]
    model = Question
    form_class = QuestionForm
    template_name = "quizzes/question_form.html"

    def get_success_url(self):
        return self.object.quiz.get_absolute_url()


class QuestionDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = ["mentor"]
    model = Question
    template_name = "quizzes/question_confirm_delete.html"

    def get_success_url(self):
        return self.object.quiz.get_absolute_url()
