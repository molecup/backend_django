from datetime import date, datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import permission_required
from django.utils import timezone
from django.db.models import Q
from .models import Match, MatchEvent, TeamParticipationMatch, Player, LocalLeague, Team
from django import forms

# Filter Form for the list page
class MatchFilterForm(forms.Form):
    local_league = forms.ModelChoiceField(queryset=LocalLeague.objects.all(), required=False, label="Local League", empty_label="All Leagues")
    team = forms.ModelChoiceField(queryset=Team.objects.all(), required=False, label="Team", empty_label="All Teams")
    date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="Date")

# Form for adding/editing events
class MatchEventForm(forms.ModelForm):
    class Meta:
        model = MatchEvent
        fields = ['team_match', 'minute', 'event_type', 'player']
        widgets = {
            'team_match': forms.HiddenInput(),
        }

    def __init__(self, team_participation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team_participation = team_participation
        
        # Pre-set the team match
        self.fields['team_match'].initial = team_participation
        
        # Filter players to only show players in this team
        self.fields['player'].queryset = Player.objects.filter(team=team_participation.team).order_by('last_name', 'first_name')
        self.fields['player'].label = "Player"
        self.fields['minute'].widget.attrs.update({'style': 'width: 60px;', 'min': 0, 'max': 120})
        self.fields['event_type'].widget.attrs.update({'style': 'width: 100%;'})

@staff_member_required
def match_list_view(request):
    matches = Match.objects.select_related('stadium').prefetch_related('participations__team', 'participations__team__local_league').all().order_by('-datetime')
    
    form = MatchFilterForm(request.GET)
    if form.is_valid():
        if form.cleaned_data['local_league']:
            matches = matches.filter(participations__team__local_league=form.cleaned_data['local_league']).distinct()
        if form.cleaned_data['team']:
            matches = matches.filter(participations__team=form.cleaned_data['team']).distinct()
        if form.cleaned_data['date']:
            matches = matches.filter(datetime__date=form.cleaned_data['date'])

    today = timezone.localtime(timezone.now()).date()

    context = {
        'matches': matches,
        'form': form,
        'today': today,
        'title': 'Match Management'
    }
    return render(request, 'admin/matches/custom_match_list.html', context)

@staff_member_required
def match_edit_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    participations = list(match.participations.select_related('team').all())

    # Calculate elapsed minutes if live
    elapsed_minutes = 0
    form_initial_minute = 0
    if match.status == 'LIVE' and match.datetime:
        now = timezone.localtime(timezone.now())
        start = timezone.localtime(match.datetime)
        delta = now - start
        elapsed_minutes = int(delta.total_seconds() / 60)
        if elapsed_minutes < 0: elapsed_minutes = 0
        
        # Cap the initial form value at 90 to prevent accidental high values
        form_initial_minute = elapsed_minutes if elapsed_minutes <= 90 else 90

    if request.method == 'POST':
        # Handle Event Creation
        if 'add_event' in request.POST:
            tp_id = request.POST.get('team_participation_id')
            tp = get_object_or_404(TeamParticipationMatch, id=tp_id, match=match)
            
            # Reconstruct the prefix used in the GET view
            prefix = f'team_{tp.id}'
            form = MatchEventForm(tp, request.POST, prefix=prefix)
            
            if form.is_valid():
                form.save()
                return redirect('custom_match_edit', match_id=match.id)
            else:
                pass 

        elif 'delete_event' in request.POST:
            event_id = request.POST.get('event_id')
            event = get_object_or_404(MatchEvent, id=event_id, team_match__match=match)
            event.delete()
            return redirect('custom_match_edit', match_id=match.id)
            
        elif 'update_status' in request.POST:
             new_status = request.POST.get('status')
             if new_status in dict(Match.STATUS_CHOICES):
                 match.status = new_status
                 match.save()
                 return redirect('custom_match_edit', match_id=match.id)

        elif 'update_penalties' in request.POST:
            for tp in participations:
                penalties_value = request.POST.get(f'penalties_{tp.id}', '')
                if penalties_value in (None, ''):
                    penalties_value = 0
                try:
                    penalties_value = int(penalties_value)
                except (TypeError, ValueError):
                    penalties_value = 0
                tp.penalties = max(0, penalties_value)
                tp.save(update_fields=['penalties'])
            return redirect('custom_match_edit', match_id=match.id)

    
    # Existing events
    events = MatchEvent.objects.filter(team_match__match=match).select_related('player', 'team_match__team').order_by('-minute', '-id')
    
    # Create a form for each team participation
    team_forms = []
    initial_data = {'minute': form_initial_minute if form_initial_minute > 0 else 0}
    
    for tp in participations:
        form = MatchEventForm(tp, initial=initial_data, prefix=f'team_{tp.id}')
        team_forms.append({
            'team': tp.team,
            'participation': tp,
            'form': form
        })

    context = {
        'match': match,
        'participations': participations,
        'events': events,
        'team_forms': team_forms,
        'elapsed_minutes': elapsed_minutes,
        'title': f'Manage Match: {match.name}'
    }
    return render(request, 'admin/matches/custom_match_edit.html', context)
