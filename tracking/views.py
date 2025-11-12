from rest_framework import generics
from documents.models import Case
from .models import CaseTransition
from .serializers import CaseTransitionSerializer


class CaseTransitionsList(generics.ListAPIView):
    serializer_class = CaseTransitionSerializer


def get_queryset(self):
    case_id = self.kwargs['case_id']
    return CaseTransition.objects.filter(case__case_id=case_id)