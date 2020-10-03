from PIL import Image
import tempfile
import os
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.response import Response


from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer, RecipeImageSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title': 'Sample recipe',
        'time_minutes': 10,
        'price': 5.00,
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name='Main Course'):
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cabbage'):
    return Ingredient.objects.create(user=user, name=name)


def detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])
    # recipe/recipes/1 ( id )


def image_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


class PublicRecipeAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(RECIPE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create(
            email='kousik.sekar@gmail.com',
            password='pass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_Recipe(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipe = Recipe.objects.all()
        serializer = RecipeSerializer(recipe, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        user2 = get_user_model().objects.create(
            email='other@gmail.com',
            password='12344556'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)
        recipe = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipe, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_detail(self):
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredient.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_create(self):
        payload = {
            'title': 'Briyani',
            'time_minutes': 5,
            'price': 10.00,
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_recipe_tag_create(self):
        tag1 = sample_tag(user=self.user, name='tag1')
        tag2 = sample_tag(user=self.user, name='tag2')
        payload = {
            'title': 'test create multiple tags',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 5,
            'price': 10.00,
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_recipe_ingredient_create(self):
        ingredient1 = sample_ingredient(user=self.user, name='tag1')
        ingredient2 = sample_ingredient(user=self.user, name='tag2')
        payload = {
            'title': 'test create multiple tags',
            'ingredient': [ingredient1.id, ingredient2.id],
            'time_minutes': 5,
            'price': 10.00,
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredient.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(self.user, name='Curry')
        payload = {
            'title': 'Partial update',
            'tags': [new_tag.id]
        }

        url = detail_url(recipe.id)
        self.client.patch(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        payload = {
            'title': 'Full update',
            'time_minutes': 5,
            'price': 10.00
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        tags = recipe.tags.all()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])
        self.assertEqual(len(tags), 0)
        
    def test_filter_recipe_by_tags(self):
        recipe1 = sample_recipe(self.user, title='Potato curry')
        recipe2 = sample_recipe(self.user, title='curd Rice')
        tag1 = sample_tag(self.user, name='Vegan')
        tag2 = sample_tag(self.user, name='Vegetarian')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(self.user, title='Briyani')

        res = self.client.get(
            RECIPE_URL,
            {'tags':'{},{}'.format(tag1.id, tag2.id)}
        )
        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)




    class RecipeUploadImageTest(TestCase):

        def setUp(self):
            self.client = APIClient()
            self.user = get_user_model().objects.create_user(
                email='kousik.sekar@gmail.com',
                password='pass123'
            )
            self.client.force_authenticate(self.user)
            self.recipe = sample_recipe(self.user)

        def tearDown(self):
            return self.recipe.image.delete()


        def test_upload_image(self):
            url = image_url(self.recipe.id)
            with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
                img = Image.new('RGB', size=(10,10))
                img.save(ntf, format='jpeg')
                ntf.seek(0)
                res = self.client.post(url, {'image':ntf}, format='multipart')
            self.recipe.refresh_from_db()
            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            self.assertIn('image', res.data )
            self.assertTrue(os.path.exists(self.recipe.image.path))

        def test_upload_bad_image(self):
            url = image_url(self.recipe.id)
            res = self.client.post(url, {'image':'not_image'}, format='multipart')
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)












