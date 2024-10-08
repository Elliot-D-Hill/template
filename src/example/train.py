import torch
import torch.nn as nn
from torch.optim.sgd import SGD
from tqdm import tqdm

from example.checkpoint import (
    checkpoint_model,
    remove_worse_checkpoints,
    get_best_checkpoint_path,
)
from example.config import Config
from example.dataset import DataLoaders
from example.model import EmbeddingModel
from example.evaluate import evaluate_model


def make_components(config: Config):
    model = EmbeddingModel(**config.model.model_dump())
    optimizer = SGD(model.parameters(), **config.optimizer.model_dump())
    criterion = nn.BCEWithLogitsLoss()
    return model, optimizer, criterion


def train_model(dataloaders: DataLoaders, config: Config) -> None:
    model, optimizer, criterion = make_components(config=config)
    model_device = torch.device(config.trainer.device)
    model.to(model_device)
    progress_bar = tqdm(range(config.trainer.max_epochs), desc="Epoch")
    min_val_loss = float("inf")
    for epoch in progress_bar:
        for inputs, labels in dataloaders.train:
            inputs = inputs.to(model_device)
            labels = labels.to(model_device)
            optimizer.zero_grad()
            outputs = model(inputs)
            train_loss = criterion(outputs, labels)
            train_loss.backward()
            optimizer.step()
        if epoch % config.trainer.eval_every_n_epochs == 0:
            val_loss = evaluate_model(
                model=model,
                dataloader=dataloaders.val,
                metrics={"val_loss": criterion},
                device=model_device,
            )
        if val_loss["val_loss"] < min_val_loss:
            min_val_loss = val_loss["val_loss"]
            checkpoint_model(
                path=config.checkpoint.path,
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                train_loss=train_loss.item(),
                val_loss=min_val_loss,
                model_config=config.model,
                optimizer_config=config.optimizer,
            )
        progress_bar.set_postfix_str(
            f"train loss: {train_loss.item():.4f}; val loss: {val_loss['val_loss']:.4f}"
        )
    best_checkpoint_path = get_best_checkpoint_path(config.checkpoint)
    remove_worse_checkpoints(
        best_checkpoint_path, checkpoint_path=config.checkpoint.path
    )
