"use client";

/**
 * FG-03 バーコードスキャン（設計仕様書 3.3.1・表3-8 #1〜#3・#8）。
 * カメラ映像から JAN13 だけをデコードし、onDetected(code) を呼ぶところまでを担当する。
 * 購入リストへの追加・金額計算は親（pos/page.tsx）の手入力と同じ処理に任せる（表3-8 #9）。
 */

import { useEffect, useRef, useState } from "react";
import { BrowserMultiFormatReader, IScannerControls } from "@zxing/browser";
import { BarcodeFormat, DecodeHintType } from "@zxing/library";

type Props = {
  onDetected: (code: string) => Promise<void>;
  disabled: boolean; // 手入力の応答待ち中など
};

const SAME_CODE_INTERVAL_MS = 1000; // 同一コードは直前の読取から1秒間は無視

export default function ScanArea({ onDetected, disabled }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const controlsRef = useRef<IScannerControls | null>(null);
  const lastReadRef = useRef({ code: "", at: 0 });
  const inFlightRef = useRef(false);
  // コールバックはカメラ起動時に1度だけ登録されるため、最新の値は ref 経由で参照する
  const onDetectedRef = useRef(onDetected);
  const disabledRef = useRef(disabled);
  onDetectedRef.current = onDetected;
  disabledRef.current = disabled;

  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleStart() {
    if (!videoRef.current) return;
    setError(null);
    try {
      const hints = new Map([[DecodeHintType.POSSIBLE_FORMATS, [BarcodeFormat.EAN_13]]]);
      const reader = new BrowserMultiFormatReader(hints);
      controlsRef.current = await reader.decodeFromConstraints(
        { video: { facingMode: "environment" } }, // 背面カメラ
        videoRef.current,
        (result) => {
          if (!result) return; // 読み取れなかったフレーム（チェックディジット不一致もここ）
          const code = result.getText();
          const now = Date.now();
          const last = lastReadRef.current;
          lastReadRef.current = { code, at: now };

          if (code === last.code && now - last.at < SAME_CODE_INTERVAL_MS) return; // 二重読取
          if (inFlightRef.current || disabledRef.current) return; // 応答待ち中の読取は無視

          inFlightRef.current = true;
          onDetectedRef.current(code).finally(() => {
            inFlightRef.current = false;
          });
        }
      );
      setRunning(true);
    } catch {
      setError("M-10: カメラを利用できません。商品コードを手入力してください");
    }
  }

  function handleStop() {
    controlsRef.current?.stop();
    controlsRef.current = null;
    setRunning(false);
  }

  // 画面を離れたらカメラを止める
  useEffect(() => () => controlsRef.current?.stop(), []);

  return (
    <div style={{ border: "1px solid #999", padding: 12, borderRadius: 8 }}>
      <video ref={videoRef} style={{ width: "100%", maxWidth: 320, background: "#000" }} muted playsInline />
      <div style={{ marginTop: 8 }}>
        <button type="button" onClick={handleStart} disabled={running}>
          カメラ起動
        </button>
        <button type="button" onClick={handleStop} disabled={!running} style={{ marginLeft: 8 }}>
          停止
        </button>
      </div>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </div>
  );
}
