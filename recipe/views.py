from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, mixins

from core.models import Tag, Ingredient, Recipe
from . import serializers


class BaseRecipeAttrViewSet(mixins.ListModelMixin, mixins.CreateModelMixin,
                            viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get_queryset(self):
        """overriding the queryset method to list the query objects"""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset= queryset.filter(recipe__isnull=False)
            
        return queryset.filter(user=self.request.user).order_by('-name').distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Create your views here.
class TagViewSet(BaseRecipeAttrViewSet):
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.RecipeSerializer
    queryset = Recipe.objects.all()

    def _params_to_int(self, qs):
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredient')
        queryset = self.queryset

        if tags:
            tags_id = self._params_to_int(tags)
            queryset = queryset.filter(tags__id__in=tags_id)
        if ingredients:
            ingredient_id = self._params_to_int(ingredients)
            queryset = queryset.filter(ingredient__id__in=ingredient_id)

        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return serializers.RecipeDetailSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
