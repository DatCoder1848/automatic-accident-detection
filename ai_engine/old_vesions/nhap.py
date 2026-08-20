
import torch

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print("CUDA sẵn sàng không?:", torch.cuda.is_available())
    print("Tên card đồ họa:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Không tìm thấy")