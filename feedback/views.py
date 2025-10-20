from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from .models import Feedback
from .serializers import FeedbackSerializer

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [AllowAny]
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def create(self, request, *args, **kwargs):
        """Handle feedback creation with proper error handling for constraints"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Set user if authenticated
            if request.user.is_authenticated:
                serializer.save(user=request.user)
            else:
                serializer.save()
                
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            
        except IntegrityError as e:
            # Handle the unique constraint error gracefully
            if 'feedback_user_id_order_id_e4cdcb6b_uniq' in str(e):
                return Response(
                    {
                        "error": "You have already submitted feedback for this order. Each customer can only submit one feedback per order.",
                        "code": "DUPLICATE_FEEDBACK"
                    }, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    {"error": f"Database error: {str(e)}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()
    
    def update(self, request, *args, **kwargs):
        """Handle feedback update with proper permissions"""
        instance = self.get_object()
        
        # Check if user owns this feedback
        if request.user.is_authenticated and instance.user != request.user:
            return Response(
                {"error": "You can only edit your own feedback"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """Handle feedback deletion with proper permissions"""
        instance = self.get_object()
        
        # Check if user owns this feedback
        if request.user.is_authenticated and instance.user != request.user:
            return Response(
                {"error": "You can only delete your own feedback"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='order/(?P<order_id>[^/.]+)')
    def get_by_order(self, request, order_id=None):
        """Get feedback for a specific order"""
        try:
            feedback = Feedback.objects.filter(order_id=order_id).first()
            if feedback:
                serializer = self.get_serializer(feedback)
                return Response(serializer.data)
            else:
                return Response(
                    {"error": "No feedback found for this order"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )