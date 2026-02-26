import json
import argparse
import random

def generate_witness(steps, output_file):
    # Giả lập tạo witness cho HKSC-4096
    # Trong thực tế, đây sẽ là các bước di chuyển của quân mã trong không gian 3D 16x16x16
    print(f"Generating witness for {steps} steps...")
    
    # Giả sử mỗi bước là một tọa độ [x, y, z]
    path = []
    current = [0, 0, 0]
    path.append(list(current))
    
    for _ in range(steps - 1):
        # Di chuyển ngẫu nhiên giả lập quân mã (chỉ để minh họa cấu trúc JSON)
        move = random.choice([[2,1,0], [1,2,0], [0,2,1], [0,1,2], [2,0,1], [1,0,2]])
        sign = [random.choice([1, -1]) for _ in range(3)]
        next_pos = [(current[i] + move[i] * sign[i]) % 16 for i in range(3)]
        path.append(next_pos)
        current = next_pos

    witness = {
        "step_count": steps,
        "path": path,
        "root": "0x" + "f" * 64 # Giả lập Merkle root
    }

    with open(output_file, 'w') as f:
        json.dump(witness, f, indent=4)
    
    print(f"Witness saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=256)
    parser.add_argument("--output", type=str, default="input_256.json")
    args = parser.parse_args()
    generate_witness(args.steps, args.output)
