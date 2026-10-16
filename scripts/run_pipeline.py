from fetch_fpl_data import build_data_pipeline
from train_fdr_model import train_categorical_glm
from predict_expected_points import generate_ev_matrix


def run_pipeline():
    build_data_pipeline()
    train_categorical_glm()
    generate_ev_matrix()


if __name__ == "__main__":
    run_pipeline()
