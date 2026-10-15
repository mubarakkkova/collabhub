"""Fill the DB with test campaigns: python manage.py seed_campaigns 10."""

import random
from datetime import timedelta
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils import timezone

from apps.campaigns.models import Campaign, CampaignPlatform, CampaignStatus
from apps.users.models import Niche, UserRole


class Command(BaseCommand):
    """Creates test campaigns for business users."""

    help = "Create test campaigns with random niches, budgets and dates."

    BRANDS = ("Aru", "Nomad", "Altyn", "Tumar", "Qyran", "Dala")
    GOALS = ("launch", "sale", "review", "giveaway", "collab")
    MIN_LENGTH_DAYS = 7
    MAX_LENGTH_DAYS = 90
    MAX_START_SHIFT_DAYS = 20
    MIN_BUDGET = 100_000
    MAX_BUDGET = 3_000_000

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "count",
            type=int,
            help="How many campaigns to create.",
        )

    def make_title(self, business_id: int, taken: set[tuple[int, str]]) -> str:
        """A title this business does not use yet."""
        base = f"{random.choice(self.BRANDS)} {random.choice(self.GOALS)}"
        title = base
        number = 1
        while (business_id, title) in taken:
            number += 1
            title = f"{base} {number}"
        taken.add((business_id, title))
        return title

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        count: int = options["count"]
        if count <= 0:
            raise CommandError("count must be greater than 0.")

        user_model = get_user_model()
        businesses = list(
            user_model.objects.filter(role=UserRole.BUSINESS, is_active=True)
        )
        if not businesses:
            raise CommandError(
                "No business users. Create them in the admin panel first."
            )

        niches: list[Niche] = list(Niche.objects.filter(deleted_at__isnull=True))
        if not niches:
            raise CommandError("No niches. Create them in the admin panel first.")

        taken: set[tuple[int, str]] = set(
            Campaign.objects.values_list("business_id", "title")
        )
        today = timezone.now().date()
        campaigns: list[Campaign] = []

        for _ in range(count):
            business = random.choice(businesses)
            shift = random.randint(
                -self.MAX_START_SHIFT_DAYS, self.MAX_START_SHIFT_DAYS
            )
            length = random.randint(self.MIN_LENGTH_DAYS, self.MAX_LENGTH_DAYS)
            start_date = today + timedelta(days=shift)
            budget = random.randint(self.MIN_BUDGET, self.MAX_BUDGET) // 1000 * 1000
            campaigns.append(
                Campaign(
                    business=business,
                    niche=random.choice(niches),
                    title=self.make_title(business.pk, taken),
                    platform=random.choice(CampaignPlatform.values),
                    budget=Decimal(budget),
                    start_date=start_date,
                    end_date=start_date + timedelta(days=length),
                    status=random.choice(CampaignStatus.values),
                )
            )
        Campaign.objects.bulk_create(campaigns)

        if options["verbosity"] >= 2:
            for campaign in campaigns:
                self.stdout.write(f"Created {campaign}:{campaign.budget}")
        self.stdout.write(self.style.SUCCESS(f"Created{len(campaigns)} campaigns"))
