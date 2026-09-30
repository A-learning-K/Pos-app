// Jest 設定（Next.js 公式の next/jest を使用。TS/TSX の変換・CSS の無視を自動で行う）
const nextJest = require("next/jest");

const createJestConfig = nextJest({ dir: "./" });

module.exports = createJestConfig({
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  // "@/lib/api" のようなパス別名を使っている場合に解決する（tsconfig の paths と同じ前提）
  moduleNameMapper: { "^@/(.*)$": "<rootDir>/$1" },
  // Playwright のテスト（e2e/）は Jest では実行しない
  // macOS の AppleDouble ファイル（外部SSD等でファイル操作時に自動生成される「._」始まりの影ファイル）を除外
  // 例：__tests__/._T-012_pos_header.test.tsx がテストスイートとして誤認識され Syntax Error になる問題への対策
  testPathIgnorePatterns: ["<rootDir>/node_modules/", "<rootDir>/e2e/", "<rootDir>/_archive/", /(^|\/)\._/.source],
});
