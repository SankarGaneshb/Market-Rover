from sqlalchemy import select
from src.config.database import async_session, engine
from src.data.models import Promoter, Base

async def seed_data():
    """Seeds the initial promoter data into the SQL database."""
    initial_promoters = [
        {"symbol": "LLOYDSME", "company_name": "Lloyds Metals And Energy Limited", "governance_score": 3.8, "total_shares": 504.6,
         "holding_pct": 65.5, "pledged_pct": 12.4, "skin_in_the_game": 42.4, "skin_layer1": 65.5, "skin_layer2": 12.4,
         "survival_score": 45.0, "intent_label": "Survival", "trust_signal": "Caution", "release_create_ratio": 0.6},
        {"symbol": "DEEPAKFERT", "company_name": "Deepak Fertilizers And Petrochemicals", "governance_score": 6.2, "total_shares": 126.9,
         "holding_pct": 48.0, "pledged_pct": 34.5, "skin_in_the_game": 72.8, "skin_layer1": 48.0, "skin_layer2": 34.5,
         "survival_score": 82.0, "intent_label": "Growth", "trust_signal": "Optimistic", "release_create_ratio": 1.2},
        {"symbol": "NOCIL", "company_name": "NOCIL Limited", "governance_score": 8.5, "total_shares": 166.6,
         "holding_pct": 33.8, "pledged_pct": 4.1, "skin_in_the_game": 91.2, "skin_layer1": 33.8, "skin_layer2": 4.1,
         "survival_score": 95.0, "intent_label": "Growth", "trust_signal": "Strong", "release_create_ratio": 2.5},
        {"symbol": "AJANTPHARM", "company_name": "Ajanta Pharma", "governance_score": 9.1, "total_shares": 126.0,
         "holding_pct": 66.2, "pledged_pct": 0.0, "skin_in_the_game": 100.0, "skin_layer1": 66.2, "skin_layer2": 0.0,
         "survival_score": 98.0, "intent_label": "Growth", "trust_signal": "Clean", "release_create_ratio": 1.0},
        {"symbol": "CAMLINFINE", "company_name": "Camlin Fine Sciences", "governance_score": 4.5, "total_shares": 167.5,
         "holding_pct": 48.0, "pledged_pct": 18.9, "skin_in_the_game": 52.5, "skin_layer1": 48.0, "skin_layer2": 18.9,
         "survival_score": 28.0, "intent_label": "Survival", "trust_signal": "Critical", "release_create_ratio": 0.1},
    ]

    async with async_session() as session:
        async with session.begin():
            # Check if already seeded
            result = await session.execute(select(Promoter).limit(1))
            if result.scalars().first():
                print("Database already contains promoter data. Skipping seed.")
                return

            print(f"Seeding {len(initial_promoters)} promoters...")
            for p_data in initial_promoters:
                promoter = Promoter(**p_data)
                session.add(promoter)
            
        await session.commit()
    print("Seeding complete.")
