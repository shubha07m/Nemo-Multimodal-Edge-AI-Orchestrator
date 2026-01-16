import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType

input_model_path = "yolov8s-worldv2.onnx"
output_model_path = "yolov8s-worldv2-int8.onnx"

print(f"Compressing {input_model_path} -> {output_model_path}...")

quantize_dynamic(
    input_model_path,
    output_model_path,
    weight_type=QuantType.QUInt8
)

print("Done! You can now use the INT8 model.")
