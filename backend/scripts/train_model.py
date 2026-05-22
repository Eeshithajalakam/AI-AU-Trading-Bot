"""CLI: train XAU LSTM model."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import settings
from services.training_runner import run_training


async def main():
    Path(settings.MODEL_DIR).mkdir(parents=True, exist_ok=True)
    print("Starting training (60d GC=F data)...")
    result = await run_training(epochs=30, period="60d")
    print("Done:", result)


if __name__ == "__main__":
    asyncio.run(main())
