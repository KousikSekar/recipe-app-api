from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """test the unauthorized  user to be unsuccessful"""
        res = self.client.get(INGREDIENT_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTest(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='kousik.sekar@gmail.com',
            password='testpass123',
            name='Kousik'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='chilly')
        Ingredient.objects.create(user=self.user, name='Turmeric')

        res = self.client.get(INGREDIENT_URL)

        ingredient = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredient, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limmited_to_user(self):
        user2 = get_user_model().objects.create_user(
            email= 'other@yahoo.com',
            password= 'pass123',
            name = 'other'
        )
        Ingredient.objects.create(user=user2, name='chilly')
        ing = Ingredient.objects.create(user=self.user, name='cherry')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ing.name)

    def test_create_ingredient_successful(self):
        payload = {'name': 'cabbage'}
        res = self.client.post(INGREDIENT_URL, payload)
        ing = Ingredient.objects.filter(
            user = self.user,
            name = payload['name']
        ).exists()
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ing)

    def test_create_ingredient_invalid(self):
        payload = {'name':''}
        res = self.client.post(INGREDIENT_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)







