import os
import math
import numpy as np
from PIL import Image
import subprocess
import zlib  # 압축을 위한 모듈 추가


def extract_streams(input_video, video_stream, audio_stream):
    # 비디오 스트림 추출 (오디오 제거)
    subprocess.run(
        ["ffmpeg", "-i", input_video, "-c:v", "copy", "-an", video_stream], check=True
    )

    # 오디오 스트림 추출 (비디오 제거)
    subprocess.run(
        ["ffmpeg", "-i", input_video, "-c:a", "copy", "-vn", audio_stream], check=True
    )

    print(f"비디오 스트림: {video_stream}, 오디오 스트림: {audio_stream} 추출 완료.")


def binary_to_image(binary_data, output_image_path):
    # 바이너리 데이터를 압축
    compressed_data = zlib.compress(binary_data)
    data_length = len(compressed_data)

    # 데이터 길이를 첫 4바이트에 저장 (빅 엔디언)
    length_bytes = data_length.to_bytes(4, byteorder="big")
    combined_data = length_bytes + compressed_data

    data_array = np.frombuffer(combined_data, dtype=np.uint8)

    # 3의 배수로 패딩
    padding_size = (-len(data_array)) % 3
    if padding_size > 0:
        data_array = np.concatenate(
            [data_array, np.zeros(padding_size, dtype=np.uint8)]
        )

    total_pixels = len(data_array) // 3
    img_width = int(math.ceil(math.sqrt(total_pixels)))
    img_height = int(math.ceil(total_pixels / img_width))

    required_pixels = img_width * img_height
    padding_pixels = required_pixels - (len(data_array) // 3)
    if padding_pixels > 0:
        data_array = np.concatenate(
            [data_array, np.zeros(padding_pixels * 3, dtype=np.uint8)]
        )

    # (높이, 너비, 3) 형태로 재구성
    pixel_array = data_array.reshape((img_height, img_width, 3))

    # 이미지 생성 및 저장 (PNG 형식으로 저장하여 압축)
    image = Image.fromarray(pixel_array, "RGB")
    image.save(output_image_path, format="PNG")  # 형식을 PNG로 변경
    print(
        f'바이너리 데이터를 이미지로 인코딩하여 "{output_image_path}"로 저장하였습니다. 이미지 크기: {img_width} x {img_height} 픽셀'
    )


def image_to_binary(image_path):
    image = Image.open(image_path)
    img_width, img_height = image.size
    pixel_data = np.array(image).reshape(-1, 3).flatten()

    # 바이너리 데이터 복원
    combined_bytes = bytes(pixel_data)

    # 첫 4바이트에서 데이터 길이 추출
    if len(combined_bytes) < 4:
        print(
            f"Error: {image_path}의 이미지 데이터가 너무 작아 데이터 길이를 추출할 수 없습니다."
        )
        return b""

    data_length = int.from_bytes(combined_bytes[:4], byteorder="big")
    compressed_data = combined_bytes[4 : 4 + data_length]

    # 데이터 압축 해제
    binary_data = zlib.decompress(compressed_data)

    print(
        f'"{image_path}"에서 바이너리 데이터를 복원하였습니다. 데이터 길이: {len(binary_data)} 바이트'
    )
    return binary_data


def binary_to_video(binary_data, output_video_path):
    with open(output_video_path, "wb") as f:
        f.write(binary_data)
    print(f'바이너리 데이터를 동영상 파일로 "{output_video_path}"에 저장하였습니다.')


def binary_to_audio(binary_data, output_audio_path):
    with open(output_audio_path, "wb") as f:
        f.write(binary_data)
    print(f'바이너리 데이터를 오디오 파일로 "{output_audio_path}"에 저장하였습니다.')


def combine_streams(video_stream, audio_stream, output_video):
    # 임시 파일로 비디오와 오디오 스트림 저장
    temp_video = "temp_video_stream.h264"
    temp_audio = "temp_audio_stream.aac"

    with open(temp_video, "wb") as f:
        f.write(video_stream)
    with open(temp_audio, "wb") as f:
        f.write(audio_stream)

    # FFmpeg를 사용하여 스트림을 합쳐 MP4 파일 생성
    subprocess.run(
        ["ffmpeg", "-i", temp_video, "-i", temp_audio, "-c", "copy", output_video],
        check=True,
    )

    print(f'비디오와 오디오 스트림을 합쳐 "{output_video}"를 생성하였습니다.')

    # 임시 파일 삭제
    os.remove(temp_video)
    os.remove(temp_audio)


def video_to_binary(video_path):
    with open(video_path, "rb") as f:
        binary_data = f.read()
    print(
        f'"{video_path}"를 바이너리 데이터로 변환하였습니다. 데이터 길이: {len(binary_data)} 바이트'
    )
    return binary_data


def audio_to_binary(audio_path):
    with open(audio_path, "rb") as f:
        binary_data = f.read()
    print(
        f'"{audio_path}"를 바이너리 데이터로 변환하였습니다. 데이터 길이: {len(binary_data)} 바이트'
    )
    return binary_data


def compare_data(original, restored, name="데이터"):
    print(f"원본 {name} 길이: {len(original)} 바이트")
    print(f"복원된 {name} 길이: {len(restored)} 바이트")
    if original == restored:
        print(f"{name}이(가) 정확히 복원되었습니다.")
    else:
        print(f"{name}이(가) 일치하지 않습니다.")


if __name__ == "__main__":
    # 파일 경로 설정
    input_video_path = "input_video.mp4"
    video_stream_path = "video_stream.h264"
    audio_stream_path = "audio_stream.aac"
    video_image_path = "video_compressed.png"  # 확장자를 PNG로 변경
    audio_image_path = "audio_compressed.png"  # 확장자를 PNG로 변경
    restored_video_stream_path = "restored_video_stream.h264"
    restored_audio_stream_path = "restored_audio_stream.aac"
    restored_video_path = "restored_video.mp4"

    try:
        # 1. MP4 파일에서 비디오와 오디오 스트림 추출
        extract_streams(input_video_path, video_stream_path, audio_stream_path)

        # 2. 스트림을 바이너리로 변환
        video_binary = video_to_binary(video_stream_path)
        audio_binary = audio_to_binary(audio_stream_path)

        # 3. 바이너리 데이터를 이미지로 인코딩
        binary_to_image(video_binary, video_image_path)
        binary_to_image(audio_binary, audio_image_path)

        # 4. 이미지에서 바이너리 데이터 복원
        restored_video_binary = image_to_binary(video_image_path)
        restored_audio_binary = image_to_binary(audio_image_path)

        # 5. 원본과 복원된 데이터 비교
        compare_data(video_binary, restored_video_binary, "비디오 데이터")
        compare_data(audio_binary, restored_audio_binary, "오디오 데이터")

        # 6. 복원된 스트림을 합쳐 MP4 파일 생성
        combine_streams(
            restored_video_binary, restored_audio_binary, restored_video_path
        )

    except subprocess.CalledProcessError as e:
        print("FFmpeg 명령 실행 중 오류가 발생했습니다.")
        print(f"명령: {' '.join(e.cmd)}")
        print(f"리턴 코드: {e.returncode}")
        print(f"오류 메시지: {e.stderr if e.stderr else '출력되지 않음'}")
    except Exception as e:
        print("예기치 않은 오류가 발생했습니다.")
        print(str(e))
