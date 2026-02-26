# HKSC-4096

HyperKnight Supercube Cryptosystem (`16x16x16 = 4096` cells).

Bản này được nâng cấp để bám sát ý tưởng bạn đưa ra: không chỉ mã hóa block 4096 bytes, mà còn có **planner mô phỏng Rubik/knight** với:
- 3 trường hợp tỉ lệ bước (bằng nhau, mã ít hơn, mã nhiều hơn),
- tỉ lệ động theo segment,
- biến thể quân cờ (`knight/bishop/rook/queen/king`) ở mức mobility abstraction,
- nhiều agent đồng thời,
- sự kiện adversarial định kỳ.

## Kiến trúc

### 1) Cipher layer (dùng thực tế)
- `HKSC4096Cipher` mã hóa theo block 4096 bytes.
- Hoán vị dựa trên **keyed 3D knight-walk** trên không gian `16^3`.
- Nhiều vòng substitution + permutation.
- `scrypt` để dẫn xuất khóa từ passphrase.
- Xác thực toàn vẹn bằng `HMAC-SHA3-256`.

### 2) Planner layer (mô phỏng ý tưởng Rubik/knight)
- `HKSCPlanner` tạo transcript hash xác định từ cấu hình planner.
- Transcript được trộn vào keystream/domain separation của cipher.
- Nếu decrypt với planner config khác encrypt sẽ bị từ chối.

## CLI

### Encrypt / Decrypt
```bash
python hksc4096.py encrypt -i plain.bin -o secret.hksc -p "my-pass" \
  --piece knight --agents 2 --ratio-mode dynamic \
  --dynamic-schedule "512:1:1,512:1:8,512:7:1"

python hksc4096.py decrypt -i secret.hksc -o recovered.bin -p "my-pass" \
  --piece knight --agents 2 --ratio-mode dynamic \
  --dynamic-schedule "512:1:1,512:1:8,512:7:1"
```

### Planner simulation only
```bash
python hksc4096.py simulate --seed demo --cells 1024 \
  --piece queen --agents 3 --ratio-mode knight_more --ratio-den 7
```

## Test

```bash
python -m unittest discover -s tests -v
```

## Lưu ý bảo mật

- Đây là thiết kế experimental/R&D.
- Mô hình Rubik trong planner là abstraction hash-chain (không phải Rubik group solver đầy đủ).
- Không nên dùng cho dữ liệu tối mật production nếu chưa audit độc lập.
