import asyncio
from .routes.gerar_catalogo_diario import gerar_catalogo_diario
from datetime import datetime

async def scheduler_por_intervalo():
    print("⏰ Scheduler de catálogo iniciado...")
    while True:
        agora = datetime.now()
        print(f"\n🔹 Checando necessidade de gerar catálogo às {agora.strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            await gerar_catalogo_diario()
        except Exception as e:
            print(f"❌ Erro no scheduler: {e}")

        # Aguarda 1 minuto antes da próxima verificação
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(scheduler_por_intervalo())
