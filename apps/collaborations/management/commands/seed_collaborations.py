"""Fill the DB with test collaborations: python manage.py seed_collaborations 25."""

import random
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from apps.campaigns.models import Campaign
from apps.collaborations.models import (
    Collaboration,
    CollaborationStatus,
    CollaborationStatusHistory,
)
from apps.users.models import UserRole


class Command(BaseCommand):
    """Creates collaborations between existing campaigns and bloggers."""

    help = "Create test collaborations and their status history."

    MESSAGE = (
        "Hi! I love your brand and would be happy to make a review.",
        "My audience is 70% women 18-30, they like this kind of products.",
        "I can make 1 reels and 3 stories during the first week.",
        "I already worked with similar brands, can send statistics.",
        "Ready to start right after we sign the contract.",
        "",
    )
    MIN_PRICE = 20_000
    MAX_PRICE = 500_000

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "count",
            type=int,
            help="How many collaborations to create.",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        count: int = options["count"]
        if count <= 0:
            raise CommandError("count must be greater than 0.")

        campaigns: list[Campaign] = list(Campaign.objects.all())
        bloggers: list[Any] = list(
            get_user_model().objects.filter(role=UserRole.BLOGGER)
        )
        if not campaigns or not bloggers:
            raise CommandError("No campaigns or bloggers. Fill users/campaigns first.")

        # 1 query: all pairs that already exist (UniqueConstraint).
        existing: set[tuple[int, int]] = set(
            Collaboration.objects.filter(deleted_at__isnull=True).values_list(
                "campaign_id", "blogger_id"
            )
        )
        free_pairs: list[tuple[Campaign, Any]] = [
            (campaign, blogger)
            for campaign in campaigns
            for blogger in bloggers
            if (campaign.id, blogger.id) not in existing
        ]
        if len(free_pairs) < count:
            self.stdout.write(
                self.style.WARNING(f"Only {len(free_pairs)} free pairs left")
            )
        random.shuffle(free_pairs)

        # Objects in memory only, no queries inside the loop.
        collaborations: list[Collaboration] = [
            Collaboration(
                campaign=campaign,
                blogger=blogger,
                message=random.choice(self.MESSAGE),
                offered_price=Decimal(
                    random.randint(self.MIN_PRICE, self.MAX_PRICE) // 1000 * 1000
                ),
                status=random.choice(CollaborationStatus.values),
            )
            for campaign, blogger in free_pairs[:count]
        ]
        # bulk_create does NOT call save(), so the history is created by hand.
        Collaboration.objects.bulk_create(collaborations)

        history: list[CollaborationStatusHistory] = []
        for collaboration in collaborations:
            history.append(
                CollaborationStatusHistory(
                    collaboration=collaboration,
                    old_status="",
                    new_status=CollaborationStatus.SENT,
                )
            )
            if collaboration.status != CollaborationStatus.SENT:
                history.append(
                    CollaborationStatusHistory(
                        collaboration=collaboration,
                        old_status=CollaborationStatus.SENT,
                        new_status=collaboration.status,
                    )
                )
            if options["verbosity"] >= 2:
                self.stdout.write(f"Created {collaboration}")
        CollaborationStatusHistory.objects.bulk_create(history)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {len(collaborations)} collaborations "
                f"and {len(history)} history rows"
            )
        )
