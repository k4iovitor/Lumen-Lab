"""
Modelos de dados para o módulo de autenticação de estudantes do LumenLab.

Define a entidade `StudentProfile`, que estende o modelo nativo de usuário
do Django (`User`) para armazenar atributos pedagógicos e metadados da
conta Google (Gmail) do aluno, como data de nascimento e identificador OAuth.
"""
from django.db import models
from django.contrib.auth.models import User


class StudentProfile(models.Model):
    """
    Perfil do Estudante vinculado a uma conta Google (Gmail).

    Atributos:
        user (OneToOneField): Vínculo unívoco com o usuário padrão do Django.
        first_name (CharField): Primeiro nome do estudante.
        last_name (CharField): Sobrenome do estudante.
        date_of_birth (DateField): Data de nascimento para adequação pedagógica de faixa etária.
        gmail (EmailField): Endereço de e-mail Gmail único utilizado na autenticação Google.
        google_id (CharField): Identificador unívoco do usuário fornecido pelo Google (claim 'sub').
        avatar_url (URLField): URL pública da imagem de perfil associada à conta Google.
        created_at (DateTimeField): Registro de data e hora em que a conta foi criada na plataforma.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='Usuário Django'
    )
    first_name = models.CharField('Nome', max_length=150)
    last_name = models.CharField('Sobrenome', max_length=150)
    date_of_birth = models.DateField('Data de Nascimento')
    gmail = models.EmailField('E-mail Google (Gmail)', unique=True)
    google_id = models.CharField('Identificador Google (sub)', max_length=255, unique=True)
    avatar_url = models.URLField('URL da Foto de Perfil', max_length=500, blank=True, default='')
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil do Estudante'
        verbose_name_plural = 'Perfis dos Estudantes'
        ordering = ['-created_at']

    def __str__(self):
        """Representação textual legível do perfil do estudante."""
        return f'{self.first_name} {self.last_name} ({self.gmail})'
