# app/scheduler_jobs.py
from .models import User, AccessGroup, Zone
from datetime import datetime
import pytz

# Esta função continua a mesma, calculando a lista de usuários bloqueados
def get_all_blocked_user_ids():
    inactive_user_ids = {user.id for user in User.query.filter_by(is_active=False).all()}
    users_outside_schedule_ids = set()
    restricted_groups = AccessGroup.query.filter_by(is_24h=False).all()
    tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz)
    current_time = now.time()
    current_weekday = now.weekday()
    weekday_map = {0: 'day_mon', 1: 'day_tue', 2: 'day_wed', 3: 'day_thu', 4: 'day_fri', 5: 'day_sat', 6: 'day_sun'}
    
    for group in restricted_groups:
        is_day_allowed = getattr(group, weekday_map.get(current_weekday))
        is_time_allowed = group.start_time <= current_time <= group.end_time
        if not (is_day_allowed and is_time_allowed):
            for user in group.users:
                users_outside_schedule_ids.add(user.id)
    return inactive_user_ids.union(users_outside_schedule_ids)

# A tarefa principal agora orquestra as chamadas
def check_schedules_and_update_ha():
    from run import app
    # Importamos o serviço aqui dentro da função para ajudar a evitar importações circulares
    from .services.ha_service import update_disabled_ids_in_ha

    with app.app_context():
        # print("\n--- SCHEDULER: Iniciando tarefa de verificação de horários ---")
        try:
            # 1. Calcula a lista de usuários bloqueados PRIMEIRO
            all_blocked_ids = get_all_blocked_user_ids()
            
            # 2. Processa cada zona, passando a lista já calculada
            all_zones = Zone.query.all()
            for zone in all_zones:
                # print(f"SCHEDULER: Processando zona '{zone.name}'...")
                # 3. Passa a lista como argumento para a função de serviço
                update_disabled_ids_in_ha(zone, all_blocked_ids)

            # print("--- SCHEDULER: Tarefa de verificação concluída. ---\n")
        except Exception as e:
            print(f"--- SCHEDULER: ERRO CRÍTICO ao executar a tarefa: {e} ---")