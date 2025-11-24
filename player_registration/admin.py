import datetime
from django.contrib import admin

from .models import DeletionRequest, Player, Parent, PlayerList

class ParentInline(admin.StackedInline):
    model = Parent
    extra = 0
    verbose_name = "Parent of the Player"
    verbose_name_plural = "Parent of the Player"
    can_delete = False
    show_change_link = True
    classes = ['collapse']



# Register your models here.
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'user__email', 'last_name', 'first_name', 'shirt_number', 'position', 'shirt_size', 'player_list__name')
    search_fields = ('first_name', 'last_name', 'shirt_number', 'player_list__name', 'user__email', 'code_fiscal')
    list_filter = ('position', 'player_list__name', 'player_list__team__local_league__name')
    list_editable = ('shirt_number', 'position', 'shirt_size')

    fieldsets = (
        (None, {
            'fields': ('user', 'player_list')
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'code_fiscal')
        }),
        ('Sport Info', {
            'fields': ('shirt_number', 'shirt_size', 'position')
        }),
    )
    search_help_text = "Search by first name, last name, shirt number, player list name, user email, or code fiscal."

    inlines = [ParentInline]

@admin.register(PlayerList)
class PlayerListAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'manager', 'registration_token', 'team')
    search_fields = ('name', 'manager__email', 'team__name')
    list_filter = ('team__local_league__name',)
    list_editable = ('name', 'team')
    readonly_fields = ('registration_token',)
    search_help_text = "Search by team name or manager email."

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        """
        return {}
    list_display = ('id', 'player__user__email', 'last_name', 'first_name', 'code_fiscal')
    search_fields = ('first_name', 'last_name', 'code_fiscal')
    list_editable = ('first_name', 'last_name', 'code_fiscal')

    search_help_text = "Search by first name, last name, or fiscal code."



@admin.register(DeletionRequest)
class DeletionRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'player_to_be_deleted', 'requested_by', 'requested_at', 'status')
    search_fields = ('player_to_be_deleted__user__email', 'requested_by__email', 'status')
    list_filter = ('status',)
    readonly_fields = ('requested_at', 'deletion_info', 'player_to_be_deleted', 'requested_by', 'status')
    search_help_text = "Search by player to be deleted email, requested by email, or status."
    
    actions = ['fullfill_deletion_request', 'reject_deletion_request']

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @admin.action(description='Fulfill selected deletion requests')
    def fullfill_deletion_request(self, request, queryset):
        for deletion_request in queryset.filter(status='PENDING'):
            deletion_request.status = 'APPROVED'
            deletion_request.deletion_info = f"Player {deletion_request.player_to_be_deleted} deleted on {datetime.datetime.now()} by admin {request.user.email}."
            deletion_request.save()
            player = deletion_request.player_to_be_deleted

            user = player.user
            player.delete()
            #also delete the user if they are not managing any player list
            if not hasattr(user, 'player_list_manager'):
                user.delete()
                
            # Delete the player
            # Update the deletion request status

    @admin.action(description='Reject selected deletion requests')
    def reject_deletion_request(self, request, queryset):
        queryset.filter(status='PENDING').update(status='REJECTED')