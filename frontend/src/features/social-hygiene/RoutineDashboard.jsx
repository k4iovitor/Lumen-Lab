import React, { useState, useEffect, useMemo } from 'react';
import { apiService } from '../../services/api';

export const RoutineDashboard = () => {
  // Retorna a data de hoje no fuso horário local formatada como 'YYYY-MM-DD'
  const getTodayIso = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  // Retorna o horário atual no formato 'HH:MM' arredondado para os próximos minutos
  const getUpcomingTimeStr = () => {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    const nextMinutes = Math.ceil((minutes + 5) / 15) * 15;
    if (nextMinutes >= 60) {
      const nextHour = (hours + 1) % 24;
      return `${String(nextHour).padStart(2, '0')}:00`;
    }
    return `${String(hours).padStart(2, '0')}:${String(nextMinutes).padStart(2, '0')}`;
  };

  const todayIso = useMemo(() => getTodayIso(), []);

  // Estado da agenda: inicia ZERADA como especificado
  const [habits, setHabits] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  // Navegação no tempo: offset de semanas em relação à semana atual (0 = semana atual)
  const [weekOffset, setWeekOffset] = useState(0);

  // Data selecionada na visualização da agenda (formato 'YYYY-MM-DD')
  const [selectedDate, setSelectedDate] = useState(todayIso);

  // Estado do formulário de criação de novo hábito
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newDate, setNewDate] = useState(todayIso);
  const [newTime, setNewTime] = useState(getUpcomingTimeStr());
  const [newKind, setNewKind] = useState('foco');
  const [formError, setFormError] = useState('');

  // Estado de Metas de Tempo de Tela e Reserva de Afazeres (persistido no banco de dados)
  const [screenGoal, setScreenGoal] = useState({
    dailyLimitMinutes: 240, // 4 horas padrão (limite máximo estrito)
    dailyLimitFormatted: '4h 00m',
    gamesVideoLimitMinutes: 180, // 3h (75%)
    gamesVideoLimitFormatted: '3h 00m',
    socialMediaLimitMinutes: 60, // 1h (25%)
    socialMediaLimitFormatted: '1h 00m',
    choresReservedMinutes: 180, // 3h reservadas para afazeres
    choresReservedFormatted: '3h 00m',
    gamesVideoUsedMinutes: 40,
    gamesVideoUsedFormatted: '40m',
    socialMediaUsedMinutes: 50,
    socialMediaUsedFormatted: '50m',
    studyUsedMinutes: 105,
    studyUsedFormatted: '1h 45m',
    totalUsedMinutes: 90,
    totalUsedFormatted: '1h 30m',
    remainingMinutes: 150,
    remainingFormatted: '2h 30m',
    usedPercentage: 38,
    isOverLimit: false,
    isGamesOverLimit: false,
    isSocialOverLimit: false,
  });

  // Estados de pausa consciente
  const [isPauseActive, setIsPauseActive] = useState(false);
  const [pauseSeconds, setPauseSeconds] = useState(15 * 60);

  // Carrega hábitos e meta de tempo de tela do backend ao montar
  useEffect(() => {
    let isMounted = true;
    const fetchInitialData = async () => {
      setIsLoading(true);
      const [serverHabits, serverGoal] = await Promise.all([
        apiService.getHabits(),
        apiService.getScreenTimeGoal(),
      ]);

      if (isMounted) {
        if (serverHabits) setHabits(serverHabits);
        if (serverGoal) setScreenGoal(serverGoal);
        setIsLoading(false);
      }
    };
    fetchInitialData();
    return () => { isMounted = false; };
  }, []);

  // Temporizador regressivo em tempo real para a Pausa Consciente
  useEffect(() => {
    let timer = null;
    if (isPauseActive && pauseSeconds > 0) {
      timer = setInterval(() => {
        setPauseSeconds(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            setIsPauseActive(false);
            return 15 * 60;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isPauseActive, pauseSeconds]);

  // Atualiza a meta diária de tela (com teto estrito de 4 horas e proporção 75%/25%)
  const handleLimitChange = async (e) => {
    const minutes = Number(e.target.value);
    // Aplica o teto máximo estrito de 4 horas (240 minutos)
    const cappedMinutes = Math.min(240, Math.max(30, minutes));

    // Atualização otimista no frontend
    const gamesLimit = Math.round(cappedMinutes * 0.75);
    const socialLimit = cappedMinutes - gamesLimit;
    const totalUsed = screenGoal.gamesVideoUsedMinutes + screenGoal.socialMediaUsedMinutes;
    const remaining = Math.max(0, cappedMinutes - totalUsed);

    setScreenGoal(prev => ({
      ...prev,
      dailyLimitMinutes: cappedMinutes,
      dailyLimitFormatted: `${Math.floor(cappedMinutes / 60)}h ${cappedMinutes % 60 ? (cappedMinutes % 60) + 'm' : '00m'}`,
      gamesVideoLimitMinutes: gamesLimit,
      gamesVideoLimitFormatted: `${Math.floor(gamesLimit / 60)}h ${gamesLimit % 60 ? (gamesLimit % 60) + 'm' : '00m'}`,
      socialMediaLimitMinutes: socialLimit,
      socialMediaLimitFormatted: socialLimit >= 60 ? `${Math.floor(socialLimit / 60)}h ${socialLimit % 60 ? (socialLimit % 60) + 'm' : '00m'}` : `${socialLimit}m`,
      remainingMinutes: remaining,
      remainingFormatted: `${Math.floor(remaining / 60)}h ${remaining % 60 ? (remaining % 60) + 'm' : '00m'}`,
      usedPercentage: Math.min(100, Math.round((totalUsed / cappedMinutes) * 100)),
      isOverLimit: totalUsed > cappedMinutes,
      isGamesOverLimit: prev.gamesVideoUsedMinutes > gamesLimit,
      isSocialOverLimit: prev.socialMediaUsedMinutes > socialLimit,
    }));

    // Persiste no banco de dados através da API
    const updated = await apiService.updateScreenTimeGoal({ dailyLimitMinutes: cappedMinutes });
    if (updated) {
      setScreenGoal(updated);
    }
  };

  // Permite ao estudante ajustar o tempo reservado para cumprimento de afazeres
  const handleChoresChange = async (minutes) => {
    setScreenGoal(prev => ({
      ...prev,
      choresReservedMinutes: minutes,
      choresReservedFormatted: `${Math.floor(minutes / 60)}h ${minutes % 60 ? (minutes % 60) + 'm' : '00m'}`,
    }));
    await apiService.updateScreenTimeGoal({ choresReservedMinutes: minutes });
  };

  // Calcula os 7 dias da semana com base no weekOffset e no calendário real do estudante
  const weekDays = useMemo(() => {
    const now = new Date();
    now.setDate(now.getDate() + weekOffset * 7);

    const currentDay = now.getDay(); // 0: Dom, 1: Seg, 2: Ter, ..., 6: Sáb
    const distToMon = currentDay === 0 ? -6 : 1 - currentDay;
    const monday = new Date(now);
    monday.setDate(now.getDate() + distToMon);

    const labels = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
    const fullLabels = [
      'Segunda-feira', 'Terça-feira', 'Quarta-feira',
      'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo'
    ];
    const monthNames = [
      'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];

    return labels.map((label, idx) => {
      const d = new Date(monday);
      d.setDate(monday.getDate() + idx);

      const year = d.getFullYear();
      const month = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const isoString = `${year}-${month}-${day}`;

      return {
        label,
        fullLabel: fullLabels[idx],
        dayNumber: d.getDate(),
        monthName: monthNames[d.getMonth()],
        year,
        isoString,
        isToday: isoString === todayIso,
        hasHabits: habits.some(h => h.date === isoString),
      };
    });
  }, [weekOffset, habits, todayIso]);

  // Rótulo dinâmico do Mês e Ano do cabeçalho da semana
  const weekHeaderLabel = useMemo(() => {
    if (!weekDays.length) return '';
    const firstDay = weekDays[0];
    const lastDay = weekDays[6];
    if (firstDay.monthName === lastDay.monthName && firstDay.year === lastDay.year) {
      return `${firstDay.monthName} de ${firstDay.year}`;
    }
    if (firstDay.year === lastDay.year) {
      return `${firstDay.monthName} - ${lastDay.monthName} de ${firstDay.year}`;
    }
    return `${firstDay.monthName} (${firstDay.year}) - ${lastDay.monthName} (${lastDay.year})`;
  }, [weekDays]);

  // Informações completas do dia selecionado
  const selectedDayInfo = useMemo(() => {
    const foundInWeek = weekDays.find(d => d.isoString === selectedDate);
    if (foundInWeek) return foundInWeek;

    const [y, m, d] = selectedDate.split('-').map(Number);
    const dateObj = new Date(y, m - 1, d);
    const fullLabels = [
      'Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira',
      'Quinta-feira', 'Sexta-feira', 'Sábado'
    ];
    const monthNames = [
      'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ];
    return {
      label: fullLabels[dateObj.getDay()].slice(0, 3),
      fullLabel: fullLabels[dateObj.getDay()],
      dayNumber: d,
      monthName: monthNames[m - 1],
      year: y,
      isoString: selectedDate,
      isToday: selectedDate === todayIso,
      hasHabits: habits.some(h => h.date === selectedDate),
    };
  }, [weekDays, selectedDate, todayIso, habits]);

  // Filtra hábitos específicos para a data selecionada
  const dayHabits = useMemo(() => {
    return habits
      .filter(h => h.date === selectedDate)
      .sort((a, b) => (a.time || '').localeCompare(b.time || ''));
  }, [habits, selectedDate]);

  // Navegação no calendário
  const handlePrevWeek = () => setWeekOffset(prev => prev - 1);
  const handleNextWeek = () => setWeekOffset(prev => prev + 1);
  const handleGoToToday = () => {
    setWeekOffset(0);
    setSelectedDate(todayIso);
  };

  // Alterna status de conclusão de um hábito
  const toggleHabit = async (id) => {
    const target = habits.find(h => h.id === id);
    if (!target) return;

    const newFinished = !target.finished;
    setHabits(prev =>
      prev.map(h => (h.id === id ? { ...h, finished: newFinished } : h))
    );

    await apiService.toggleHabit(id, newFinished);
  };

  // Remove um hábito do banco de dados e da interface
  const handleDeleteHabit = async (id, e) => {
    e.stopPropagation();
    setHabits(prev => prev.filter(h => h.id !== id));
    await apiService.deleteHabit(id);
  };

  // Submissão do formulário de criação com validação temporal
  const handleAddHabit = async (e) => {
    e.preventDefault();
    setFormError('');

    const trimmedTitle = newTitle.trim();
    if (!trimmedTitle) {
      setFormError('Por favor, informe o título do hábito.');
      return;
    }

    if (!newDate) {
      setFormError('Selecione uma data válida para a atividade.');
      return;
    }

    // Não permite agendar em dias anteriores a hoje
    if (newDate < todayIso) {
      setFormError('A data não pode ser anterior ao dia de hoje.');
      return;
    }

    // Se a data for hoje, valida se o horário é igual ou posterior ao atual
    if (newDate === todayIso) {
      const now = new Date();
      const currentH = now.getHours();
      const currentM = now.getMinutes();
      const [inputH, inputM] = newTime.split(':').map(Number);

      if (inputH < currentH || (inputH === currentH && inputM < currentM)) {
        setFormError('O horário selecionado já passou. Escolha um horário a partir do momento atual.');
        return;
      }
    }

    const habitPayload = {
      title: trimmedTitle,
      description: newDescription.trim() || (newKind === 'foco' ? 'Sessão de estudos focados sem celular.' : 'Navegação intencional e consciente.'),
      date: newDate,
      time: newTime || '14:00',
      kind: newKind,
    };

    const savedHabit = await apiService.createHabit(habitPayload);

    if (savedHabit) {
      setHabits(prev => [...prev, savedHabit]);
      setSelectedDate(newDate);

      const [ny, nm, nd] = newDate.split('-').map(Number);
      const targetDateObj = new Date(ny, nm - 1, nd);
      const nowDateObj = new Date();
      const diffDays = Math.round((targetDateObj - nowDateObj) / (1000 * 60 * 60 * 24));
      const targetOffset = Math.floor((diffDays + nowDateObj.getDay() - 1) / 7);
      if (targetOffset !== weekOffset) {
        setWeekOffset(targetOffset);
      }
    }

    setNewTitle('');
    setNewDescription('');
    setShowAddForm(false);
  };

  const startPause = () => {
    if (isPauseActive) {
      setIsPauseActive(false);
      setPauseSeconds(15 * 60);
    } else {
      setIsPauseActive(true);
      setPauseSeconds(15 * 60);
    }
  };

  const formatPauseTimer = (sec) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${String(s).padStart(2, '0')}`;
  };

  // Cálculo de porcentagem de cada categoria em relação ao seu limite proporcional
  const gamesPercentage = useMemo(() => {
    if (!screenGoal.gamesVideoLimitMinutes) return 0;
    return Math.min(100, Math.round((screenGoal.gamesVideoUsedMinutes / screenGoal.gamesVideoLimitMinutes) * 100));
  }, [screenGoal]);

  const socialPercentage = useMemo(() => {
    if (!screenGoal.socialMediaLimitMinutes) return 0;
    return Math.min(100, Math.round((screenGoal.socialMediaUsedMinutes / screenGoal.socialMediaLimitMinutes) * 100));
  }, [screenGoal]);

  return (
    <div className="routine-dashboard">
      {/* Banner Principal com Cores Vibrantes */}
      <div className="routine-banner">
        <div className="routine-banner-icon">
          <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"></path>
          </svg>
        </div>
        <div>
          <span className="eyebrow" style={{ fontSize: '10px', letterSpacing: '1.2px', color: '#7042f4', fontWeight: 800 }}>
            EQUILÍBRIO & GESTÃO DA ATENÇÃO
          </span>
          <h2>Higiene Digital e Hábitos de Desconexão</h2>
          <p>Organize suas metas de tela (máximo 4h/dia), reserve tempo protegido para afazeres e construa autonomia com a tecnologia.</p>
        </div>
        <div className="routine-demo" style={{ background: '#7042f4', color: '#ffffff', fontWeight: 700, padding: '5px 10px', borderRadius: '8px' }}>
          AGENDA & METAS ATIVAS
        </div>
      </div>

      <div className="routine-columns">
        {/* Painel Esquerdo: Agenda de Hábitos do Estudante */}
        <div className="routine-panel">
          <div className="routine-section-heading">
            <div>
              <div className="eyebrow">AGENDA DO ESTUDANTE</div>
              <h3>Organize seus estudos e pausas</h3>
            </div>
            <button 
              className="routine-add"
              onClick={() => {
                setNewDate(selectedDate >= todayIso ? selectedDate : todayIso);
                setNewTime(getUpcomingTimeStr());
                setFormError('');
                setShowAddForm(!showAddForm);
              }}
              style={{ cursor: 'pointer' }}
            >
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 5v14M5 12h14"></path>
              </svg>
              {showAddForm ? 'Cancelar' : 'Novo hábito'}
            </button>
          </div>

          {/* Barra de Navegação do Calendário (Semana, Mês e Ano Reais) */}
          <div className="calendar-nav-bar">
            <div className="calendar-month-year">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7042f4" strokeWidth="2.2">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              <h4>{weekHeaderLabel}</h4>
            </div>
            <div className="calendar-nav-controls">
              <button 
                type="button"
                className="calendar-nav-btn"
                onClick={handlePrevWeek}
                title="Semana anterior"
              >
                ← Anterior
              </button>
              <button 
                type="button"
                className={`calendar-nav-btn ${weekOffset === 0 && selectedDate === todayIso ? 'calendar-today-btn' : ''}`}
                onClick={handleGoToToday}
                title="Voltar para a semana e dia de hoje"
              >
                Hoje
              </button>
              <button 
                type="button"
                className="calendar-nav-btn"
                onClick={handleNextWeek}
                title="Próxima semana"
              >
                Próxima →
              </button>
            </div>
          </div>

          {/* Formulário de Adicionar Hábito */}
          {showAddForm && (
            <form onSubmit={handleAddHabit} className="routine-form" style={{ marginTop: '16px', flexDirection: 'column', alignItems: 'stretch' }}>
              <div className="routine-form-grid">
                <label>
                  Data
                  <input 
                    type="date" 
                    value={newDate} 
                    min={todayIso}
                    onChange={e => setNewDate(e.target.value)} 
                    required
                  />
                </label>
                <label>
                  Horário
                  <input 
                    type="time" 
                    value={newTime} 
                    onChange={e => setNewTime(e.target.value)} 
                    required
                  />
                </label>
                <label className="routine-title-input">
                  Título do hábito
                  <input 
                    type="text" 
                    placeholder="Ex: Leitura offline sem notificações" 
                    value={newTitle}
                    onChange={e => setNewTitle(e.target.value)}
                    autoFocus
                    required
                  />
                </label>
                <label>
                  Tipo
                  <select 
                    value={newKind} 
                    onChange={e => setNewKind(e.target.value)}
                    style={{ border: '1.5px solid #d8b4fe', background: '#faf5ff', borderRadius: '8px', padding: '9px', color: '#6b21a8', fontWeight: 600 }}
                  >
                    <option value="foco">Foco Offline</option>
                    <option value="online">Uso Consciente</option>
                  </select>
                </label>
              </div>

              <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-end', marginTop: '10px' }}>
                <label style={{ flex: 1 }}>
                  Descrição ou notas da atividade (opcional)
                  <input 
                    type="text" 
                    placeholder="Ex: Pausa ativa para alongamento e descanso ocular de 15 minutos."
                    value={newDescription}
                    onChange={e => setNewDescription(e.target.value)}
                  />
                </label>
                <button type="submit" style={{ cursor: 'pointer', padding: '10px 18px', background: '#7042f4', color: '#fff', borderRadius: '8px', fontWeight: 700, border: 'none', boxShadow: '0 3px 10px rgba(112,66,244,0.3)' }}>
                  Salvar Hábito
                </button>
              </div>

              {formError && (
                <div style={{ color: '#e11d48', fontSize: '12px', marginTop: '8px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  {formError}
                </div>
              )}
            </form>
          )}

          {/* Seletor da Semana com Dias Reais do Estudante */}
          <div className="routine-week">
            {weekDays.map((dayItem) => {
              const isSelected = selectedDate === dayItem.isoString;
              return (
                <button
                  key={dayItem.isoString}
                  className={`${isSelected ? 'selected' : ''} ${dayItem.hasHabits ? 'has-habits' : ''}`}
                  onClick={() => setSelectedDate(dayItem.isoString)}
                  type="button"
                  title={`${dayItem.fullLabel}, ${dayItem.dayNumber} de ${dayItem.monthName}`}
                >
                  <span>{dayItem.label}</span>
                  <b>{dayItem.dayNumber}</b>
                  {dayItem.isToday && <i title="Hoje"></i>}
                </button>
              );
            })}
          </div>

          {/* Cabeçalho do Dia Selecionado */}
          <div className="routine-day-label">
            <b>
              {selectedDayInfo.isToday ? 'Hoje · ' : ''}
              {selectedDayInfo.fullLabel}, {selectedDayInfo.dayNumber} de {selectedDayInfo.monthName} de {selectedDayInfo.year}
            </b>
            <span style={{ fontWeight: 650, color: '#7042f4' }}>
              {dayHabits.length === 0
                ? 'Nenhum hábito cadastrado'
                : `${dayHabits.length} ${dayHabits.length === 1 ? 'hábito agendado' : 'hábitos agendados'}`}
            </span>
          </div>

          {/* Lista de Hábitos Agendados ou Estado Vazio */}
          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '36px', color: '#7042f4', fontSize: '13px', fontWeight: 600 }}>
              Carregando agenda do estudante...
            </div>
          ) : dayHabits.length === 0 ? (
            <div className="routine-empty-state">
              <div className="routine-empty-icon">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                  <line x1="16" y1="2" x2="16" y2="6"></line>
                  <line x1="8" y1="2" x2="8" y2="6"></line>
                  <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
              </div>
              <h4>Agenda zerada para este dia</h4>
              <p>
                Você ainda não possui atividades cadastradas em {selectedDayInfo.fullLabel.toLowerCase()}.
                Defina hábitos de estudo focado ou desconexão a partir de agora.
              </p>
              <button
                type="button"
                className="routine-empty-add-btn"
                onClick={() => {
                  setNewDate(selectedDate >= todayIso ? selectedDate : todayIso);
                  setNewTime(getUpcomingTimeStr());
                  setShowAddForm(true);
                }}
              >
                + Agendar Atividade para este Dia
              </button>
            </div>
          ) : (
            <div>
              {dayHabits.map((habit) => (
                <div 
                  key={habit.id} 
                  className={`routine-event ${habit.finished ? 'finished' : ''}`}
                >
                  <time>{habit.time}</time>
                  <div className={`routine-event-dot ${habit.kind}`}></div>
                  <div className="routine-event-content">
                    <span className={`routine-kind ${habit.kind}`}>
                      {habit.kind === 'foco' ? 'FOCO OFFLINE' : 'ONLINE CONSCIENTE'}
                    </span>
                    <h4>{habit.title}</h4>
                    <p>{habit.description}</p>
                  </div>
                  
                  {/* Botão de Conclusão */}
                  <button
                    className="routine-check"
                    onClick={() => toggleHabit(habit.id)}
                    title={habit.finished ? 'Desmarcar hábito' : 'Concluir hábito'}
                    style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                  >
                    {habit.finished && (
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    )}
                  </button>

                  {/* Botão de Exclusão */}
                  <button
                    className="routine-delete-btn"
                    onClick={(e) => handleDeleteHabit(habit.id, e)}
                    title="Excluir hábito da agenda"
                  >
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="routine-agenda-foot">
            <div className="routine-soft-dot" style={{ background: '#7042f4' }}></div>
            <span>Dica do LumenLab: Pausas ativas e blocos sem telas fortalecem sua retenção de conteúdo e equilíbrio cognitivo.</span>
          </div>
        </div>

        {/* Painel Direito: Metas de Tempo de Tela & Reserva de Afazeres */}
        <div className="routine-side">
          <div className="routine-panel screen-panel">
            <div className="routine-section-heading">
              <div>
                <div className="eyebrow" style={{ color: '#7042f4', fontWeight: 800 }}>METAS DE DESCONEXÃO</div>
                <h3>Tempo de tela diário</h3>
              </div>
              <span style={{ fontSize: '10px', background: '#f5f3ff', color: '#7042f4', padding: '4px 8px', borderRadius: '6px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                TETO MÁX: 4h/dia
              </span>
            </div>

            {/* Total e Progresso Principal */}
            <div className="screen-total">
              <span className="screen-total-val" style={{ color: screenGoal.isOverLimit ? '#e11d48' : '#7042f4' }}>
                {screenGoal.totalUsedFormatted}
              </span>
              <span className="screen-total-sub">
                de {screenGoal.dailyLimitFormatted} planejadas
              </span>
            </div>

            <div className="screen-track">
              <i style={{ 
                width: `${screenGoal.usedPercentage}%`,
                background: screenGoal.isOverLimit 
                  ? 'linear-gradient(90deg, #f43f5e, #e11d48)' 
                  : 'linear-gradient(90deg, #7042f4, #ec4899)'
              }}></i>
            </div>

            <div className="screen-remaining">
              {screenGoal.isOverLimit ? (
                <span style={{ color: '#e11d48', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  Limite diário excedido! Ative uma pausa consciente.
                </span>
              ) : (
                <>Restam <b>{screenGoal.remainingFormatted}</b> para atingir o teto de hoje.</>
              )}
            </div>

            {/* Seletor de Meta Diária (com limite máximo estrito de 4 horas) */}
            <div className="routine-limit">
              <div className="routine-limit-header">
                <span style={{ fontWeight: 700, color: '#31214e', fontSize: '13px' }}>Meta diária planejada</span>
                <span style={{ fontSize: '10px', color: '#7042f4', background: '#f5f3ff', padding: '2px 8px', borderRadius: '6px', fontWeight: 700, border: '1px solid #ddd6fe' }}>
                  Máx. 4h/dia
                </span>
              </div>
              <select 
                value={screenGoal.dailyLimitMinutes} 
                onChange={handleLimitChange}
                aria-label="Meta diária de entretenimento planejada"
              >
                <option value="240">4 horas / dia (Teto Máximo Recomendado)</option>
                <option value="210">3h 30m / dia</option>
                <option value="180">3 horas / dia</option>
                <option value="150">2h 30m / dia</option>
                <option value="120">2 horas / dia</option>
                <option value="90">1h 30m / dia</option>
                <option value="60">1 hora / dia</option>
              </select>
            </div>

            {/* Card de Reserva de Tempo para Afazeres */}
            <div style={{
              background: 'linear-gradient(135deg, #f0fdf4 0%, #ecfeff 100%)',
              border: '1.5px solid #a7f3d0',
              borderRadius: '12px',
              padding: '14px 16px',
              marginTop: '16px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#065f46" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                  </svg>
                  <span style={{ fontSize: '12px', fontWeight: 800, color: '#065f46' }}>
                    Tempo Reservado para Afazeres
                  </span>
                </div>
                <b style={{ fontSize: '13px', color: '#047857' }}>
                  {screenGoal.choresReservedFormatted}
                </b>
              </div>
              <p style={{ fontSize: '11px', color: '#047857', margin: '6px 0 0 0', lineHeight: 1.5 }}>
                Ao limitar o entretenimento em {screenGoal.dailyLimitFormatted}, você protege tempo precioso para o cumprimento de afazeres escolares e atividades offline.
              </p>
            </div>

            {/* Categorias de Entretenimento (Somente Jogos & Vídeos 75% e Redes Sociais 25%) */}
            <div className="screen-categories">
              {/* Jogos & Vídeos (Limite Proporcional de 75%: Máx 3h na meta de 4h) */}
              <div style={{ paddingBottom: '12px', borderBottom: '1px solid #f3e8ff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#7042f4', display: 'inline-block', flexShrink: 0 }}></span>
                    <span style={{ fontWeight: 700, color: '#31214e', fontSize: '13px' }}>Jogos & Vídeos</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <b style={{ fontSize: '13px', color: screenGoal.isGamesOverLimit ? '#e11d48' : '#7042f4' }}>
                      {screenGoal.gamesVideoUsedFormatted}
                    </b>
                    <span style={{ fontSize: '11px', color: '#6b7280', fontWeight: 500 }}>
                      / {screenGoal.gamesVideoLimitFormatted}
                    </span>
                    <span style={{ fontSize: '10px', background: '#f5f3ff', color: '#7042f4', padding: '1px 5px', borderRadius: '4px', fontWeight: 700, border: '1px solid #ddd6fe', marginLeft: '2px' }}>
                      75%
                    </span>
                  </div>
                </div>
                <div className="category-track" style={{ height: '7px', background: '#f3e8ff', borderRadius: '6px', overflow: 'hidden' }}>
                  <i style={{ 
                    width: `${gamesPercentage}%`, 
                    display: 'block',
                    height: '100%',
                    borderRadius: '6px',
                    background: screenGoal.isGamesOverLimit 
                      ? 'linear-gradient(90deg, #f43f5e, #e11d48)' 
                      : 'linear-gradient(90deg, #818cf8, #7042f4)',
                    transition: 'width 0.3s ease'
                  }}></i>
                </div>
              </div>

              {/* Redes Sociais (Limite Proporcional de 25%: Máx 1h na meta de 4h) */}
              <div style={{ paddingTop: '2px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ec4899', display: 'inline-block', flexShrink: 0 }}></span>
                    <span style={{ fontWeight: 700, color: '#31214e', fontSize: '13px' }}>Redes Sociais</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <b style={{ fontSize: '13px', color: screenGoal.isSocialOverLimit ? '#e11d48' : '#db2777' }}>
                      {screenGoal.socialMediaUsedFormatted}
                    </b>
                    <span style={{ fontSize: '11px', color: '#6b7280', fontWeight: 500 }}>
                      / {screenGoal.socialMediaLimitFormatted}
                    </span>
                    <span style={{ fontSize: '10px', background: '#fdf2f8', color: '#db2777', padding: '1px 5px', borderRadius: '4px', fontWeight: 700, border: '1px solid #fbcfe8', marginLeft: '2px' }}>
                      25%
                    </span>
                  </div>
                </div>
                <div className="category-track" style={{ height: '7px', background: '#fce7f3', borderRadius: '6px', overflow: 'hidden' }}>
                  <i style={{ 
                    width: `${socialPercentage}%`, 
                    display: 'block',
                    height: '100%',
                    borderRadius: '6px',
                    background: screenGoal.isSocialOverLimit 
                      ? 'linear-gradient(90deg, #f43f5e, #e11d48)' 
                      : 'linear-gradient(90deg, #f472b6, #ec4899)',
                    transition: 'width 0.3s ease'
                  }}></i>
                </div>
              </div>
            </div>

            <div className="screen-note" style={{ color: '#7e22ce', background: '#faf5ff', padding: '12px 14px', borderRadius: '10px', border: '1px solid #f3e8ff', fontWeight: 600, fontSize: '11px', lineHeight: 1.5, marginTop: '16px', display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#7e22ce" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0, marginTop: '2px' }} aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
              <span>Evite o uso de telas nos 60 minutos anteriores ao sono para proteger seu descanso profundo e capacidade de memorização.</span>
            </div>
          </div>

          {/* Cartão de Pausa Consciente com Contador Ativo */}
          <div className="routine-pause" style={{
            background: 'linear-gradient(135deg, #f5f3ff 0%, #e0e7ff 100%)',
            border: '1.5px solid #c4b5fd',
            boxShadow: '0 4px 16px rgba(112, 66, 244, 0.08)'
          }}>
            <div className="routine-pause-icon" style={{ background: '#7042f4', color: '#ffffff' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
            </div>
            <div className="eyebrow" style={{ color: '#7042f4', fontWeight: 800 }}>
              DESCONEXÃO ATIVA
            </div>
            <h3 style={{ color: '#31214e' }}>Pausa Consciente</h3>
            <p style={{ color: '#5b21b6', fontWeight: 500 }}>
              {isPauseActive 
                ? `Pausa em andamento! Descanse seus olhos longe das telas por mais ${formatPauseTimer(pauseSeconds)}.`
                : 'Ative um intervalo de 15 minutos sem telas para relaxar os olhos e recuperar o foco mental.'}
            </p>
            <button 
              onClick={startPause}
              style={{ 
                cursor: 'pointer', 
                background: isPauseActive ? 'linear-gradient(135deg, #059669, #10b981)' : 'linear-gradient(135deg, #7042f4, #9333ea)',
                color: '#ffffff',
                border: 'none',
                boxShadow: '0 4px 12px rgba(112, 66, 244, 0.35)',
                fontWeight: 700
              }}
            >
              <span>{isPauseActive ? `Pausa Ativa: ${formatPauseTimer(pauseSeconds)} (Clique para parar)` : 'Iniciar pausa de 15 min'}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M5 12h14m-5-5 5 5-5 5"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
