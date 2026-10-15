from django.db import models


class ConciergeRequest(models.Model):
    EXPERIENCE_BIOLENS = 'experience_biolens'
    WORKSPACE = 'workspace_request'
    SEARCH_INTEREST = 'search_interest'

    TYPE_CHOICES = [
        (EXPERIENCE_BIOLENS, 'Experience BioLens'),
        (WORKSPACE, 'Workspace request'),
        (SEARCH_INTEREST, 'Search interest'),
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


class Visitor(models.Model):
    """A person who went through /welcome. Identified by a random token kept in
    a long-lived cookie (mirrored in localStorage) so repeat QR scans skip the
    questions."""

    token = models.CharField(max_length=64, unique=True, db_index=True)
    directory_id = models.CharField(max_length=40, blank=True, db_index=True)
    name = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=300, blank=True)
    company = models.CharField(max_length=200, blank=True)
    company_domain = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    segment = models.CharField(max_length=40, blank=True)
    modalities = models.JSONField(default=list, blank=True)
    phases = models.JSONField(default=list, blank=True)
    geographies = models.JSONField(default=list, blank=True)
    completed = models.BooleanField(default=False)
    user_agent = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name or 'Anonymous'} — {self.company or '?'}"

    @property
    def first_name(self):
        parts = [p for p in self.name.split() if p.lower().rstrip('.') not in {'dr', 'mr', 'ms', 'mrs', 'prof', 'professor'}]
        return parts[0] if parts else ''


class DirectoryCompany(models.Model):
    """CDMO Live attendee company (seller side). Loaded by `manage.py load_directory`."""
    key = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200)
    segment = models.CharField(max_length=40, blank=True)
    domain = models.CharField(max_length=200, blank=True)
    modalities = models.JSONField(default=list, blank=True)
    exhibitor = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'directory companies'

    def __str__(self):
        return self.name


class DirectoryPerson(models.Model):
    id = models.CharField(max_length=40, primary_key=True)
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=300, blank=True)
    company = models.ForeignKey(DirectoryCompany, on_delete=models.CASCADE, related_name='people')
    email = models.CharField(max_length=254, blank=True)

    class Meta:
        verbose_name_plural = 'directory people'

    def __str__(self):
        return f"{self.name} ({self.company_id})"
