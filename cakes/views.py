from rest_framework import generics, status, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from .models import Cake, Category, CustomCake, Review
from .serializers import (
    CakeSerializer, CategorySerializer, CustomCakeSerializer,
    CakeDetailSerializer, ReviewSerializer, CakeWriteSerializer,
    CategoryWriteSerializer
)

class CakeListAPIView(generics.ListAPIView):
    queryset = Cake.objects.filter(is_available=True)
    serializer_class = CakeSerializer
    permission_classes = [AllowAny]

class CakeDetailAPIView(generics.RetrieveAPIView):
    queryset = Cake.objects.filter(is_available=True)
    serializer_class = CakeDetailSerializer
    permission_classes = [AllowAny]

class CategoryListAPIView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

class CustomCakeCreateAPIView(generics.CreateAPIView):
    queryset = CustomCake.objects.all()
    serializer_class = CustomCakeSerializer
    permission_classes = [AllowAny]

@api_view(['GET'])
@permission_classes([AllowAny])
def cake_reviews(request, cake_id):
    """Get all reviews for a specific cake"""
    cake = get_object_or_404(Cake, id=cake_id, is_available=True)
    reviews = Review.objects.filter(cake=cake).order_by('-created_at')
    serializer = ReviewSerializer(reviews, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request, cake_id):
    """Create a new review for a cake"""
    print(f"Creating review for cake {cake_id} by user {request.user}")
    print(f"Request data: {request.data}")
    
    cake = get_object_or_404(Cake, id=cake_id, is_available=True)
    
    # Allow multiple reviews from same user (validation removed as requested)
    
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        print(f"Serializer is valid, saving review")
        serializer.save(cake=cake, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        print(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def calculate_customized_price(request, cake_id):
    """Calculate the price of a cake with customizations"""
    cake = get_object_or_404(Cake, id=cake_id, is_available=True)
    customizations = request.data.get('customizations', {})
    
    try:
        price = cake.calculate_customized_price(customizations)
        return Response({'price': float(price)})
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminCakeListCreateAPIView(generics.ListCreateAPIView):
    queryset = Cake.objects.all().order_by('-created_at')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CakeWriteSerializer
        return CakeSerializer


class AdminCakeRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Cake.objects.all()
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return CakeWriteSerializer
        return CakeSerializer


class AdminCategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all().order_by('name')
    permission_classes = [permissions.IsAdminUser]

    def get_serializer_class(self):
        return CategoryWriteSerializer


class AdminCategoryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    permission_classes = [permissions.IsAdminUser]
    serializer_class = CategoryWriteSerializer
