from datetime import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Case, CaseStatus
from .serializers import CaseSerializer
from django.utils.crypto import get_random_string


class CaseListCreate(generics.ListCreateAPIView):
    queryset = Case.objects.all().order_by('-created_at')
    serializer_class = CaseSerializer


def perform_create(self, serializer):
    # generate unique case id: LGT-YYYYMMDD-<random6>
    prefix = 'LGT'
    date_part = timezone.now().strftime('%Y%m%d')
    rand = get_random_string(6).upper()
    case_id = f"{prefix}-{date_part}-{rand}"
    serializer.save(case_id=case_id)


class CaseRetrieve(generics.RetrieveAPIView):
    lookup_field = 'case_id'
    queryset = Case.objects.all()
    serializer_class = CaseSerializer