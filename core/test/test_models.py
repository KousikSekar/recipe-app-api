from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models


def sample_user(email='kousik.sekar@gmail.com', password='pass1234'):
    """Helper method to create a user """
    return get_user_model().objects.create_user(email, password)


class ModelTest(TestCase):

    def test_create_user_with_email_successful(self):
        """Test creating a new user with an email is successful"""
        email = "kousik.sekar@gmail.com"
        password = "#Password123"
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email is normalized """
        email = "kousik.sekar@GMAIL.COM"
        user = get_user_model().objects.create_user(email, 'test123')
        self.assertEqual(user.email, email.lower())

    def test_email_not_passed_must_raise_value_error(self):
        """test if a Value error is raised if email is not passed in user object"""
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test123')

    def test_create_super_user(self):
        """test the creation of superuser"""
        email = "kousik.sekar@yahoo.com"
        password = "password123"
        user = get_user_model().objects.create_superuser(email, password)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """test if the tag is string"""
        tag = models.Tag.objects.create( user=sample_user(), name='Vegan')
        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        """Test the string representation of the model"""
        ingredient = models.Ingredient.objects.create(user=sample_user(), name='Pepper')
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title = 'Mutta Kolambu',
            time_minutes = 5,
            price = 50.00,
        )
        self.assertEqual(str(recipe), recipe.title)
