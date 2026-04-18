from django import forms
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, render

from matches.models import LocalLeague
from player_registration.models import PlayerList


class MedicalCertificatePlayerListFilterForm(forms.Form):
    local_league = forms.ModelChoiceField(
        queryset=LocalLeague.objects.all().order_by("name"),
        required=False,
        label="Local League",
        empty_label="All Leagues",
    )


@staff_member_required
def medical_certificate_player_lists_view(request):
    player_lists = (
        PlayerList.objects.select_related("manager", "team__local_league")
        .annotate(
            total_players_count=Count("players", distinct=True),
            uploaded_certificates_count=Count("players__medical_certificate", distinct=True),
        )
        .order_by("team__local_league__name", "name")
    )

    form = MedicalCertificatePlayerListFilterForm(request.GET or None)
    if form.is_valid() and form.cleaned_data.get("local_league"):
        player_lists = player_lists.filter(team__local_league=form.cleaned_data["local_league"])

    context = {
        "title": "Medical Certificate Verification",
        "form": form,
        "player_lists": player_lists,
    }
    return render(
        request,
        "admin/player_registration/medical_certificate_player_lists.html",
        context,
    )


@staff_member_required
def medical_certificate_player_list_players_view(request, player_list_id):
    player_list = get_object_or_404(
        PlayerList.objects.select_related("team__local_league", "manager"),
        pk=player_list_id,
    )
    players = player_list.players.select_related("user", "medical_certificate").order_by(
        "last_name", "first_name"
    )

    context = {
        "title": f"Medical Certificates - {player_list.name}",
        "player_list": player_list,
        "players": players,
    }
    return render(
        request,
        "admin/player_registration/medical_certificate_player_list_players.html",
        context,
    )
