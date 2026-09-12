from django.db import models


class ConciergeRequest(models.Model):
    EXPERIENCE_BIOLENS = 'experience_biolens'
    WORKSPACE = 'workspace_request'

    TYPE_CHOICES = [
        (EXPERIENCE_BIOLENS, 'Experience BioLens'),
        (WORKSPACE, 'Workspace request'),
    ]

    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    FULFILLED = 'fulfilled'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (IN_PROGRESS, 'In progress'),
        (FULFILLED, 'Fulfilled'),
    ]

    request_type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    guest_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    organization = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=50, blank=True)
    details = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_request_type_display()} — {self.guest_name or 'Guest'} ({self.created_at:%Y-%m-%d %H:%M})"
