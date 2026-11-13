"""
Modelos de dados para o módulo do Chatbot Lumia em português brasileiro.

Define as entidades `SessaoChat` e `MensagemChat`, responsáveis por armazenar
o histórico conversacional, a persistência de contexto e o vínculo com os estudantes.
"""
from __future__ import annotations

import uuid
from django.db import models
from django.contrib.auth.models import User
from apps.authentication.models import StudentProfile


class SessaoChat(models.Model):
    """
    Representa uma sessão de conversa entre o estudante e a assistente socrática Lumia.

    Funcionamento:
      - Cada sessão agrupa um histórico sequencial de perguntas e respostas.
      - Utiliza um identificador UUID para garantir privacidade e evitar enumeração.
      - Vincula-se ao usuário Django autenticado e ao seu respectivo perfil pedagógico.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='Identificador da Sessão (UUID)'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessoes_chat',
        verbose_name='Usuário',
        db_column='user_id'
    )
    estudante = models.ForeignKey(
        StudentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sessoes_chat',
        verbose_name='Perfil do Estudante',
        db_column='student_id'
    )
    criado_em = models.DateTimeField(
        'Criado em',
        auto_now_add=True,
        db_column='created_at'
    )
    atualizado_em = models.DateTimeField(
        'Atualizado em',
        auto_now=True,
        db_column='updated_at'
    )

    class Meta:
        db_table = 'chatbot_sessions'
        verbose_name = 'Sessão de Chat'
        verbose_name_plural = 'Sessões de Chat'
        ordering = ['-atualizado_em']

    def __str__(self) -> str:
        """Retorna uma representação legível da sessão com o ID e o nome do usuário."""
        return f'Sessão {self.id} — {self.usuario.username}'

    # Propriedades de compatibilidade para código legado
    @property
    def user(self):
        return self.usuario

    @user.setter
    def user(self, valor):
        self.usuario = valor

    @property
    def student(self):
        return self.estudante

    @student.setter
    def student(self, valor):
        self.estudante = valor

    @property
    def created_at(self):
        return self.criado_em

    @property
    def updated_at(self):
        return self.atualizado_em


class MensagemChat(models.Model):
    """
    Representa uma mensagem individual enviada pelo usuário ou pela assistente Lumia.

    Funcionamento:
      - Armazena o papel do emissor ('usuario' ou 'assistente').
      - Contém o texto integral gerado ou enviado.
      - É ordenada cronologicamente por criado_em para exibição precisa no frontend.
    """
    ESCOLHAS_PAPEL = [
        ('user', 'Usuário'),
        ('assistant', 'Lumia'),
        ('usuario', 'Usuário'),
        ('assistente', 'Lumia'),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='Identificador da Mensagem (UUID)'
    )
    sessao = models.ForeignKey(
        SessaoChat,
        on_delete=models.CASCADE,
        related_name='mensagens',
        verbose_name='Sessão Vinculada',
        db_column='session_id'
    )
    papel = models.CharField(
        'Papel do Emissor',
        max_length=20,
        choices=ESCOLHAS_PAPEL,
        db_column='role'
    )
    conteudo = models.TextField(
        'Conteúdo da Mensagem',
        db_column='content'
    )
    criado_em = models.DateTimeField(
        'Criado em',
        auto_now_add=True,
        db_column='created_at'
    )

    class Meta:
        db_table = 'chatbot_messages'
        verbose_name = 'Mensagem de Chat'
        verbose_name_plural = 'Mensagens de Chat'
        ordering = ['criado_em']

    def __str__(self) -> str:
        """Retorna resumo textual da mensagem indicando papel e início do texto."""
        return f'[{self.papel}] {self.conteudo[:60]}'

    # Propriedades de compatibilidade para código legado
    @property
    def session(self):
        return self.sessao

    @session.setter
    def session(self, valor):
        self.sessao = valor

    @property
    def role(self):
        return self.papel

    @role.setter
    def role(self, valor):
        self.papel = valor

    @property
    def content(self):
        return self.conteudo

    @content.setter
    def content(self, valor):
        self.conteudo = valor

    @property
    def created_at(self):
        return self.criado_em


# Aliases para preservar compatibilidade integral
ChatSession = SessaoChat
ChatMessage = MensagemChat
