import random

from src.comunicacao.loss import LossSimulator


def test_zero_probability_never_drops():
    sim = LossSimulator(0.0, rng=random.Random(42))
    assert all(not sim.should_drop() for _ in range(1000))


def test_full_probability_always_drops():
    sim = LossSimulator(1.0, rng=random.Random(42))
    assert all(sim.should_drop() for _ in range(1000))


def test_partial_probability_is_deterministic_with_seed():
    sim_a = LossSimulator(0.5, rng=random.Random(123))
    sim_b = LossSimulator(0.5, rng=random.Random(123))
    seq_a = [sim_a.should_drop() for _ in range(50)]
    seq_b = [sim_b.should_drop() for _ in range(50)]
    assert seq_a == seq_b


def test_partial_probability_drops_some_but_not_all():
    sim = LossSimulator(0.5, rng=random.Random(7))
    results = [sim.should_drop() for _ in range(1000)]
    drops = sum(results)
    assert 0 < drops < 1000
