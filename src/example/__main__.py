from torch.optim import SGD
from toml import load
import polars as pl

from config import Config
from example.model import MyNetwork


def main():
    config_data = load("config.toml")
    config = Config(**config_data)
    print(config)

    X = pl.DataFrame(
        {
            "x1": [1, 3, 2, 5],
            "x2": [5, 7, 3, 2],
        }
    )
    y = pl.DataFrame({"y": [0, 1, 1, 0]})

    model = MyNetwork(
        input_dim=X.shape[1], hidden_dim=config.model.hidden_dim, output_dim=y.shape[1]
    )
    optimizer = SGD(model.parameters(), **config.optimizer.model_dump())


if __name__ == "__main__":
    main()
