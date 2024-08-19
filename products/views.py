from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Product, Category, ProductVariant, ProductStep, Uom, ProductQuantity, KitchenPoste, ProductVariantAttribute, ProductVariantAttributeValue
from .serializers import ProductSerializer, CategorySerializer, ProductVariantSerializer, ProductStepSerializer, ProductQuantityCreateSerializer,ProductQuantityUpdateSerializer, ProductVariantWriteSerializer, ProductWriteSerializer, UomSerializer, ProductQuantitySerializer,CategoryWriteSerializer, KitchenPosteSerializer, ProductVariantAttributeSerializer, ProductVariantAttributeValueSerializer

@permission_classes([IsAuthenticated])
class ProductVariantAttributeValueSet(viewsets.ModelViewSet):
    queryset = ProductVariantAttributeValue.objects.all()
    serializer_class = ProductVariantAttributeValueSerializer

@permission_classes([IsAuthenticated])
class ProductVariantAttributeSet(viewsets.ModelViewSet):
    queryset = ProductVariantAttribute.objects.all()
    serializer_class = ProductVariantAttributeSerializer

@permission_classes([IsAuthenticated])
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    permission_classes = [IsAuthenticated]  # Adjust as needed

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductWriteSerializer
        return ProductSerializer

@permission_classes([IsAuthenticated])
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(parent__isnull=True, is_displayed=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return CategoryWriteSerializer
        return CategorySerializer

@permission_classes([IsAuthenticated])
class UomViewSet(viewsets.ModelViewSet):
    queryset = Uom.objects.all()
    serializer_class = UomSerializer


@permission_classes([IsAuthenticated])
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductVariantWriteSerializer
        return ProductVariantSerializer

    def create(self, request, *args, **kwargs):
        # Print the data received in the request
        print("Received data:", request.data)
        
        # Continue with the standard create process
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def override_availability(self, request):
        try:
            product_variant_id =request.data.get('product_variant_id', None)
            product_variant = ProductVariant.objects.get(id=product_variant_id)
            is_available = request.data.get('is_available', None)
            print(is_available)
            if is_available is None:
                return Response({"error": "is_available parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
     
            # Convert to boolean
            is_available = str(is_available).lower() in ['true', '1', 'yes']

            # Override the is_available value
            product_variant.is_available = is_available
            product_variant.save()
            product_variant = ProductVariant.objects.get(id=product_variant_id)
            print(product_variant.is_available)

            return Response({
                "message": "ProductVariant availability updated successfully",
                "product_variant_id": product_variant.id,
                "is_available": product_variant.is_available
            }, status=status.HTTP_200_OK)

        except ProductVariant.DoesNotExist:
            return Response({"error": "ProductVariant not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    @action(detail=True, methods=['get'], url_path='check-availability')
    def check_availability(self, request, pk=None):
        try:
            product_variant = ProductVariant.objects.get(pk=pk)

            # Check if the product variant is available
            if not product_variant.is_available:
                return Response({"available": False}, status=status.HTTP_200_OK)

            # Check the quantity if is_quantity_check is True
            if product_variant.is_quantity_check:
                product_quantity = ProductQuantity.objects.filter(product_variant=product_variant).first()
                if product_quantity is None or product_quantity.quantity <= 0:
                    return Response({"available": False}, status=status.HTTP_200_OK)

            # If all checks pass, the product variant is available
            return Response({"available": True}, status=status.HTTP_200_OK)

        except ProductVariant.DoesNotExist:
            return Response({"error": "ProductVariant not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@permission_classes([IsAuthenticated])
class ProductStepViewSet(viewsets.ModelViewSet):
    queryset = ProductStep.objects.all()
    serializer_class = ProductStepSerializer

    @action(detail=False, methods=['get'], url_path='by-variant')
    def by_variant(self, request):
        variant_id = request.query_params.get('variant_id', None)
        if variant_id is not None:
            steps = ProductStep.objects.filter(product_variant_id=variant_id)
            serializer = self.get_serializer(steps, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "variant_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class ProductQuantityViewSet(viewsets.ModelViewSet):
    queryset = ProductQuantity.objects.all()

    def get_serializer_class(self):
        if self.action in ['create']:
            return ProductQuantityCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ProductQuantityUpdateSerializer
        return ProductQuantitySerializer
    

    @action(detail=False, methods=['get'], url_path='by-variant')
    def by_variant(self, request):
        variant_id = request.query_params.get('variant_id', None)
        if variant_id is not None:
            try:
                quantity = ProductQuantity.objects.get(product_variant_id=variant_id)
                serializer = self.get_serializer(quantity)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ProductQuantity.DoesNotExist:
                return Response({"error": "Product variant not found."}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"error": "variant_id query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
class KitchenPosteViewSet(viewsets.ModelViewSet):
    queryset = KitchenPoste.objects.all()
    serializer_class = KitchenPosteSerializer





