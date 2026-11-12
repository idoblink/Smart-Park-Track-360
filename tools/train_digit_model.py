"""
ParkTrack 360 — tools/train_digit_model.py
Trains a high-accuracy, noise-rejecting digit classifier for digits 1-8 + negative class 0.
Generates synthetic marker digits with augmentations (rotation, scale, stroke width, noise)
and negative distractors (straight lines, table edges, solid rectangles, screws, circles, corners, textures).
Saves trained model to server/digit_classifier.pkl.
"""

import os
import random
import numpy as np
import cv2
import joblib
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, accuracy_score

def generate_digit_image(digit: int, size: int = 32) -> np.ndarray:
    """Renders a single digit (1-8) centered in a size x size binary image."""
    img = np.zeros((64, 64), dtype=np.uint8)
    fonts = [
        cv2.FONT_HERSHEY_SIMPLEX,
        cv2.FONT_HERSHEY_DUPLEX,
        cv2.FONT_HERSHEY_COMPLEX,
        cv2.FONT_HERSHEY_TRIPLEX
    ]
    font = random.choice(fonts)
    scale = random.uniform(1.2, 1.8)
    thickness = random.choice([2, 3, 4, 5])
    angle = random.uniform(-15, 15)

    text = str(digit)
    (tw, th), base = cv2.getTextSize(text, font, scale, thickness)
    tx = (64 - tw) // 2 + random.randint(-2, 2)
    ty = (64 + th) // 2 + random.randint(-2, 2)
    cv2.putText(img, text, (tx, ty), font, scale, 255, thickness)

    # Handwritten variants for digit 1
    if digit == 1 and random.random() < 0.5:
        img = np.zeros((64, 64), dtype=np.uint8)
        thk = random.choice([3, 4, 5])
        if random.random() < 0.5:
            # Simple vertical line |
            x_pos = 32 + random.randint(-3, 3)
            cv2.line(img, (x_pos, 10 + random.randint(-2, 2)), (x_pos, 54 + random.randint(-2, 2)), 255, thk)
        else:
            # Hook 1 with foot
            cv2.line(img, (34, 12), (34, 52), 255, thk)
            cv2.line(img, (22, 24), (34, 12), 255, thk)
            cv2.line(img, (20, 52), (48, 52), 255, thk)

    # Rotation
    if abs(angle) > 1:
        M = cv2.getRotationMatrix2D((32, 32), angle, 1.0)
        img = cv2.warpAffine(img, M, (64, 64))

    # Crop to bounding box and normalize to 32x32
    ys, xs = np.where(img > 0)
    if len(ys) == 0:
        return np.zeros((size, size), dtype=np.float32)

    crop = img[np.min(ys):np.max(ys) + 1, np.min(xs):np.max(xs) + 1]
    h, w = crop.shape
    sc = 24.0 / max(h, w)
    nh = max(1, int(h * sc))
    nw = max(1, int(w * sc))
    resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)

    norm = np.zeros((size, size), dtype=np.uint8)
    oy = (size - nh) // 2
    ox = (size - nw) // 2
    norm[oy:oy + nh, ox:ox + nw] = resized

    # Slight elastic noise / blur
    if random.random() < 0.3:
        k = random.choice([3, 5])
        norm = cv2.GaussianBlur(norm, (k, k), 0)
        _, norm = cv2.threshold(norm, 50, 255, cv2.THRESH_BINARY)

    return (norm.astype(np.float32) / 255.0)


def generate_negative_image(size: int = 32) -> np.ndarray:
    """Generates synthetic non-digit distractors (lines, table edges, rectangles, screws, noise)."""
    img = np.zeros((64, 64), dtype=np.uint8)
    mode = random.choice(["hline", "vline", "slant", "box", "circle", "corner", "random_noise", "solid"])

    thk = random.choice([2, 3, 4, 6])
    if mode == "hline":
        y = random.randint(15, 48)
        cv2.line(img, (5, y), (59, y), 255, thk)
    elif mode == "vline":
        # Random vertical stripe or double line (distinct from single clean 1)
        x = random.randint(15, 48)
        cv2.line(img, (x, 5), (x, 59), 255, thk)
        if random.random() < 0.5:
            cv2.line(img, (x + 8, 5), (x + 8, 59), 255, thk)
    elif mode == "slant":
        cv2.line(img, (random.randint(5, 20), random.randint(5, 20)),
                      (random.randint(40, 59), random.randint(40, 59)), 255, thk)
    elif mode == "box":
        x1, y1 = random.randint(10, 20), random.randint(10, 20)
        x2, y2 = random.randint(40, 55), random.randint(40, 55)
        cv2.rectangle(img, (x1, y1), (x2, y2), 255, thk)
    elif mode == "circle":
        r = random.randint(8, 20)
        cv2.circle(img, (32, 32), r, 255, -1 if random.random() < 0.5 else thk)
    elif mode == "corner":
        cv2.line(img, (15, 15), (15, 50), 255, thk)
        cv2.line(img, (15, 50), (50, 50), 255, thk)
    elif mode == "solid":
        cv2.rectangle(img, (15, 15), (49, 49), 255, -1)
    else:
        # Speckle noise
        noise = (np.random.rand(64, 64) > 0.95).astype(np.uint8) * 255
        img = noise

    # Normalize to 32x32
    ys, xs = np.where(img > 0)
    if len(ys) == 0:
        return np.zeros((size, size), dtype=np.float32)

    crop = img[np.min(ys):np.max(ys) + 1, np.min(xs):np.max(xs) + 1]
    h, w = crop.shape
    sc = 24.0 / max(h, w)
    nh = max(1, int(h * sc))
    nw = max(1, int(w * sc))
    resized = cv2.resize(crop, (nw, nh), interpolation=cv2.INTER_AREA)

    norm = np.zeros((size, size), dtype=np.uint8)
    oy = (size - nh) // 2
    ox = (size - nw) // 2
    norm[oy:oy + nh, ox:ox + nw] = resized
    return (norm.astype(np.float32) / 255.0)


def extract_features(img_32x32: np.ndarray) -> np.ndarray:
    """Extracts a compact, rotation-robust feature vector for classification."""
    # 1. 16x16 downsampled pixel intensity (256 features)
    small = cv2.resize(img_32x32, (16, 16), interpolation=cv2.INTER_AREA).flatten()

    # 2. Horizontal and vertical projection profiles (32 + 32 = 64 features)
    h_proj = np.sum(img_32x32, axis=1) / 32.0
    v_proj = np.sum(img_32x32, axis=0) / 32.0

    # 3. Contour moments and topological loops
    uint_img = (img_32x32 * 255).astype(np.uint8)
    padded = cv2.copyMakeBorder(uint_img, 2, 2, 2, 2, cv2.BORDER_CONSTANT, value=0)
    cnts, hier = cv2.findContours(padded, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    holes = 0
    if hier is not None:
        for hh in hier[0]:
            if hh[3] != -1:
                holes += 1

    hu = cv2.HuMoments(cv2.moments(uint_img)).flatten()
    # Log transform Hu moments for scale stability
    hu_log = -np.sign(hu) * np.log10(np.abs(hu) + 1e-7)

    features = np.concatenate([small, h_proj, v_proj, [holes], hu_log])
    return features


def build_dataset(samples_per_digit: int = 500, negative_samples: int = 1500):
    X, y = [], []
    print(f"Generating synthetic digits (1-8): {samples_per_digit} samples/digit...")
    for digit in range(1, 9):
        for _ in range(samples_per_digit):
            img = generate_digit_image(digit)
            feats = extract_features(img)
            X.append(feats)
            y.append(digit)

    print(f"Generating synthetic negative noise samples: {negative_samples} samples...")
    for _ in range(negative_samples):
        img = generate_negative_image()
        feats = extract_features(img)
        X.append(feats)
        y.append(0)  # Class 0: Negative / distractor

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int32)
    return X, y


def main():
    X, y = build_dataset(samples_per_digit=600, negative_samples=1800)
    
    # Shuffle and split
    indices = np.random.permutation(len(X))
    split = int(len(X) * 0.85)
    train_idx, val_idx = indices[:split], indices[split:]
    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]

    print(f"Training Multi-Layer Perceptron on {len(X_train)} samples...")
    mlp = MLPClassifier(
        hidden_layer_sizes=(128, 64),
        activation='relu',
        solver='adam',
        max_iter=150,
        random_state=42,
        early_stopping=True,
        n_iter_no_change=10
    )
    mlp.fit(X_train, y_train)

    y_pred = mlp.predict(X_val)
    acc = accuracy_score(y_val, y_pred)
    print(f"Validation Accuracy: {acc * 100:.2f}%")
    print(classification_report(y_val, y_pred))

    out_path = os.path.join("server", "digit_classifier.pkl")
    joblib.dump(mlp, out_path)
    print(f"[SUCCESS] Trained model saved to: {out_path}")


if __name__ == "__main__":
    main()

