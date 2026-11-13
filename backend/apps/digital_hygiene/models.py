"""
Modelos de dados para o módulo de Higiene Digital e Rotina Consciente do LumenLab.

Define a entidade `Habit`, que armazena os hábitos e atividades de foco
offline ou uso online consciente planejados pelos estudantes na agenda.
Cada hábito é associado univocamente ao usuário (estudante) que o criou.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.authentication.models import StudentProfile


class Habit(models.Model):
    """
    Hábito ou atividade de rotina agendada pelo estudante.

    Atributos:
        user (ForeignKey): Vínculo com a conta de usuário padrão do Django (tabela auth_user).
        student (ForeignKey): Vínculo com o perfil de estudante (tabela authentication_studentprofile).
        title (CharField): Título descritivo do hábito (ex: 'Estudo em Modo Foco sem Celular').
        description (TextField): Orientações ou anotações pedagógicas adicionais.
        date (DateField): Data do calendário em que a atividade está programada (YYYY-MM-DD).
        time (CharField): Horário estipulado para a atividade (formato 'HH:MM').
        kind (CharField): Categoria do hábito ('foco' para Foco Offline ou 'online' para Uso Consciente).
        finished (BooleanField): Indicador booleano se a tarefa já foi concluída.
        created_at (DateTimeField): Registro da data e hora de criação da atividade.
        updated_at (DateTimeField): Registro da data e hora da última modificação.
    """
    KIND_CHOICES = [
        ('foco', 'Foco Offline'),
        ('online', 'Uso Consciente'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='digital_habits',
        verbose_name='Usuário Django'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='digital_habits',
        null=True,
        blank=True,
        verbose_name='Perfil do Estudante'
    )
    title = models.CharField('Título do Hábito', max_length=255)
    description = models.TextField('Descrição', blank=True, default='')
    date = models.DateField('Data Programada', db_index=True)
    time = models.CharField('Horário', max_length=10)
    kind = models.CharField(
        'Tipo de Atividade',
        max_length=20,
        choices=KIND_CHOICES,
        default='foco'
    )
    finished = models.BooleanField('Concluído', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        db_table = 'digital_hygiene_habits'
        verbose_name = 'Hábito de Higiene Digital'
        verbose_name_plural = 'Hábitos de Higiene Digital'
        ordering = ['date', 'time', 'id']

    def save(self, *args, **kwargs):
        """Auto-preenche o vínculo com StudentProfile se o User possuir perfil associado."""
        if self.user and hasattr(self.user, 'student_profile') and not self.student:
            self.student = self.user.student_profile
        super().save(*args, **kwargs)

    def to_dict(self):
        """Serializa os atributos do modelo em formato compatível com JSON."""
        return {
            'id': str(self.id),
            'title': self.title,
            'description': self.description,
            'date': self.date.isoformat() if self.date else '',
            'time': self.time,
            'kind': self.kind,
            'finished': self.finished,
            'userId': self.user_id,
            'studentId': self.student_id if self.student else None,
            'createdAt': self.created_at.isoformat() if self.created_at else '',
        }

    def __str__(self):
        return f'{self.title} ({self.date} às {self.time}) - Usuário: {self.user.username}'


class ScreenTimeGoal(models.Model):
    """
    Configuração e metas de tempo de tela diário e desconexão consciente do estudante.

    Define o teto diário de uso de telas (com limite máximo estrito de 4 horas = 240 minutos)
    e reserva tempo protegido para o cumprimento de afazeres escolares e atividades offline.
    A distribuição estabelece o teto de 3h para jogos/vídeos (75%) e 1h para redes sociais (25%),
    adaptando-se na proporção exata caso o estudante defina um tempo menor.

    Atributos:
        user (ForeignKey): Vínculo com a conta de usuário do Django (auth_user).
        student (ForeignKey): Vínculo com o perfil de estudante (authentication_studentprofile).
        daily_limit_minutes (IntegerField): Meta diária total de tempo de tela (máx 240 min).
        games_video_limit_minutes (IntegerField): Limite proporcional de jogos e vídeos (75%).
        social_media_limit_minutes (IntegerField): Limite proporcional de redes sociais (25%).
        chores_reserved_minutes (IntegerField): Tempo reservado para afazeres e foco offline.
        games_video_used_minutes (IntegerField): Minutos reais consumidos em jogos e vídeos hoje.
        social_media_used_minutes (IntegerField): Minutos reais consumidos em redes sociais hoje.
        study_used_minutes (IntegerField): Minutos reais consumidos em estudos e plataformas hoje.
        created_at (DateTimeField): Data de criação da meta.
        updated_at (DateTimeField): Data da última modificação.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='screen_time_goals',
        verbose_name='Usuário Django'
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name='screen_time_goals',
        null=True,
        blank=True,
        verbose_name='Perfil do Estudante'
    )
    daily_limit_minutes = models.IntegerField(
        'Meta Diária Total (minutos)',
        default=240,  # 4 horas padrão
        help_text='Limite máximo permitido: 240 minutos (4 horas por dia)'
    )
    games_video_limit_minutes = models.IntegerField(
        'Limite Jogos e Vídeos (minutos)',
        default=180  # 3 horas padrão (75%)
    )
    social_media_limit_minutes = models.IntegerField(
        'Limite Redes Sociais (minutos)',
        default=60  # 1 hora padrão (25%)
    )
    chores_reserved_minutes = models.IntegerField(
        'Tempo Reservado para Afazeres (minutos)',
        default=180  # 3 horas reservadas para estudos/tarefas
    )
    games_video_used_minutes = models.IntegerField(
        'Uso Hoje em Jogos e Vídeos (minutos)',
        default=40
    )
    social_media_used_minutes = models.IntegerField(
        'Uso Hoje em Redes Sociais (minutos)',
        default=50
    )
    study_used_minutes = models.IntegerField(
        'Uso Hoje em Estudos e Plataformas (minutos)',
        default=105  # 1h 45m
    )
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        db_table = 'digital_hygiene_screen_goals'
        verbose_name = 'Meta de Tempo de Tela'
        verbose_name_plural = 'Metas de Tempo de Tela'
        ordering = ['-updated_at']

    def calculate_proportions(self):
        """
        Ajusta a distribuição na proporção exata:
        - Teto máximo absoluto de 240 minutos (4 horas).
        - 75% para jogos e vídeos (máximo de 3h na meta de 4h).
        - 25% para redes sociais (máximo de 1h na meta de 4h).
        """
        # Garante o teto estrito de 4 horas (240 minutos)
        if self.daily_limit_minutes > 240:
            self.daily_limit_minutes = 240
        elif self.daily_limit_minutes < 30:
            self.daily_limit_minutes = 30

        # Proporção exata: 3/4 (75%) para jogos e vídeos, 1/4 (25%) para redes sociais
        self.games_video_limit_minutes = int(round(self.daily_limit_minutes * 0.75))
        self.social_media_limit_minutes = self.daily_limit_minutes - self.games_video_limit_minutes

    def save(self, *args, **kwargs):
        if self.user and hasattr(self.user, 'student_profile') and not self.student:
            self.student = self.user.student_profile
        self.calculate_proportions()
        super().save(*args, **kwargs)

    @staticmethod
    def format_duration(minutes):
        """Converte minutos em string legível 'Xh Ym' ou 'Ym'."""
        h = minutes // 60
        m = minutes % 60
        if h > 0 and m > 0:
            return f'{h}h {m:02d}m'
        elif h > 0:
            return f'{h}h 00m'
        return f'{m}m'

    def to_dict(self):
        """Serializa a meta e o consumo atual em formato JSON completo."""
        total_used = self.games_video_used_minutes + self.social_media_used_minutes
        remaining_minutes = max(0, self.daily_limit_minutes - total_used)
        used_percentage = min(100, int(round((total_used / self.daily_limit_minutes) * 100))) if self.daily_limit_minutes > 0 else 0

        return {
            'id': self.id,
            'userId': self.user_id,
            'studentId': self.student_id if self.student else None,
            'dailyLimitMinutes': self.daily_limit_minutes,
            'dailyLimitFormatted': self.format_duration(self.daily_limit_minutes),
            'gamesVideoLimitMinutes': self.games_video_limit_minutes,
            'gamesVideoLimitFormatted': self.format_duration(self.games_video_limit_minutes),
            'socialMediaLimitMinutes': self.social_media_limit_minutes,
            'socialMediaLimitFormatted': self.format_duration(self.social_media_limit_minutes),
            'choresReservedMinutes': self.chores_reserved_minutes,
            'choresReservedFormatted': self.format_duration(self.chores_reserved_minutes),
            'gamesVideoUsedMinutes': self.games_video_used_minutes,
            'gamesVideoUsedFormatted': self.format_duration(self.games_video_used_minutes),
            'socialMediaUsedMinutes': self.social_media_used_minutes,
            'socialMediaUsedFormatted': self.format_duration(self.social_media_used_minutes),
            'studyUsedMinutes': self.study_used_minutes,
            'studyUsedFormatted': self.format_duration(self.study_used_minutes),
            'totalUsedMinutes': total_used,
            'totalUsedFormatted': self.format_duration(total_used),
            'remainingMinutes': remaining_minutes,
            'remainingFormatted': self.format_duration(remaining_minutes),
            'usedPercentage': used_percentage,
            'isOverLimit': total_used > self.daily_limit_minutes,
            'isGamesOverLimit': self.games_video_used_minutes > self.games_video_limit_minutes,
            'isSocialOverLimit': self.social_media_used_minutes > self.social_media_limit_minutes,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else '',
        }

    def __str__(self):
        return f'Meta de Tela: {self.daily_limit_minutes}min (Jogos: {self.games_video_limit_minutes}m, Redes: {self.social_media_limit_minutes}m) - {self.user.username}'

