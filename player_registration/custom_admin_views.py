from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from matches.models import LocalLeague
from player_registration.models import MedicalCertificate, PlayerList


class MedicalCertificatePlayerListFilterForm(forms.Form):
    local_league = forms.ModelChoiceField(
        queryset=LocalLeague.objects.all().order_by("name"),
        required=False,
        label="Local League",
        empty_label="All Leagues",
    )


@permission_required('player_registration.view_medicalcertificate', raise_exception=True)
def medical_certificate_player_lists_view(request):
    today = timezone.localdate()
    valid_certificate_filter = Q(players__medical_certificate__expires_at__gte=today) | Q(
        players__medical_certificate__expires_at__isnull=True
    )

    player_lists = (
        PlayerList.objects.select_related("manager", "team__local_league")
        .annotate(
            total_players_count=Count("players", distinct=True),
            uploaded_certificates_count=Count(
                "players__medical_certificate",
                filter=valid_certificate_filter,
                distinct=True,
            ),
            verified_certificates_count=Count(
                "players__medical_certificate",
                filter=Q(players__medical_certificate__is_verified=True) & valid_certificate_filter,
                distinct=True,
            ),
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


@permission_required('player_registration.view_medicalcertificate', raise_exception=True)
def medical_certificate_player_list_players_view(request, player_list_id):
    player_list = get_object_or_404(
        PlayerList.objects.select_related("team__local_league", "manager"),
        pk=player_list_id,
    )

    if request.method == "POST":
        if not request.user.has_perm('player_registration.change_medicalcertificate'):
            raise PermissionDenied("You do not have permission to modify medical certificates.")
        
        action = request.POST.get("action")
        player_id = request.POST.get("player_id")
        player = get_object_or_404(player_list.players.select_related("medical_certificate"), pk=player_id)

        if action == "delete_certificate":
            if hasattr(player, "medical_certificate"):
                player.medical_certificate.delete()
                messages.success(
                    request,
                    f"Medical certificate deleted for {player.first_name or ''} {player.last_name or ''}".strip(),
                )
            else:
                messages.warning(request, "The selected player has no medical certificate to delete.")

            return redirect(
                reverse(
                    "medical-certificate-player-list-players",
                    kwargs={"player_list_id": player_list.id},
                )
            )

        if action == "upload_certificate":
            certificate_file = request.FILES.get("certificate_file")
            expires_at_input = request.POST.get("expires_at", "").strip()

            if not certificate_file:
                messages.error(request, "Please choose a certificate file before uploading.")
                return redirect(
                    reverse(
                        "medical-certificate-player-list-players",
                        kwargs={"player_list_id": player_list.id},
                    )
                )

            if not expires_at_input:
                messages.error(request, "Please provide the certificate expiry date.")
                return redirect(
                    reverse(
                        "medical-certificate-player-list-players",
                        kwargs={"player_list_id": player_list.id},
                    )
                )

            expires_at = None
            if expires_at_input:
                expires_at = parse_date(expires_at_input)
                if expires_at is None:
                    messages.error(request, "Invalid expiry date format.")
                    return redirect(
                        reverse(
                            "medical-certificate-player-list-players",
                            kwargs={"player_list_id": player_list.id},
                        )
                    )

            if hasattr(player, "medical_certificate"):
                player.medical_certificate.delete()

            MedicalCertificate.objects.create(
                player=player,
                file=certificate_file,
                expires_at=expires_at,
                submitted_at=timezone.now(),
            )
            messages.success(
                request,
                f"Medical certificate uploaded for {player.first_name or ''} {player.last_name or ''}".strip(),
            )
            return redirect(
                reverse(
                    "medical-certificate-player-list-players",
                    kwargs={"player_list_id": player_list.id},
                )
            )

        if action == "verify_certificate":
            if hasattr(player, "medical_certificate"):
                player.medical_certificate.is_verified = True
                player.medical_certificate.save()
                messages.success(
                    request,
                    f"Medical certificate verified for {player.first_name or ''} {player.last_name or ''}".strip(),
                )
            else:
                messages.warning(request, "The selected player has no medical certificate to verify.")

            return redirect(
                reverse(
                    "medical-certificate-player-list-players",
                    kwargs={"player_list_id": player_list.id},
                )
            )

    players = player_list.players.select_related("user", "medical_certificate").order_by(
        "last_name", "first_name"
    )

    context = {
        "title": f"Medical Certificates - {player_list.name}",
        "player_list": player_list,
        "players": players,
        "today": timezone.localdate(),
    }
    return render(
        request,
        "admin/player_registration/medical_certificate_player_list_players.html",
        context,
    )
