# GHKB Hardware Sourcing

> **License note:** the hardware designs in this repository (`pcb/`, `case/`,
> KiCad projects, schematics, PCB layouts, footprints, and the 3D-printed
> enclosure source) are licensed under the **CERN Open Hardware Licence v2 –
> Strongly Reciprocal (CERN-OHL-S)**. You may manufacture and sell hardware
> based on these designs, but any product or derived design you convey to others
> must have its corresponding design source made available under CERN-OHL-S.
> See `LICENSE-HARDWARE`. (Software/firmware is separately licensed under
> GPL-3.0 — see `LICENSE`.)

조달용 부품 목록. 기준: `pcb/keyboard.kicad_pcb`(리버서블 1종)과
`case/source/params.py`의 v1 설계. 수량은 **양쪽 하프 합산 기준**이며,
소모품(다이오드/소켓/나사)은 여유분을 포함해 사는 것을 전제로 팩 단위
링크를 걸었다. 링크와 가격은 2026-07 조회 기준이라 품절 시 동일 검색어로
대체하면 된다.

부품별 정확한 대응 규격의 근거는 `pcb/ergogen/footprints/*.js` 헤더에
문서화되어 있다 (ceoloide 풋프린트가 명시하는 호환 부품).

## PCB 주문

| 항목 | 값 |
|---|---|
| 보드 | `pcb/keyboard.kicad_pcb` — 리버서블 1종, 좌/우 공용 |
| 외형 | 149.2 × 105.8 mm |
| 층수 / 두께 | 2층 / 1.6 mm |
| 표면처리 | HASL(무연)이면 충분, ENIG 선택사항 |
| 수량 | 2장 사용 (대부분 업체 최소 5장 — 여분은 자연 확보) |
| 특이사항 | M2.2 NPTH 6개 포함. `PWR1`(전원 스위치) 패드가 보드 엣지에 걸리는 것은 사이드 마운트 부품의 의도된 배치 (무넷 기계 패드) |

거버/드릴 파일은 발주 직전 `kicad-cli`로 생성한다 (업체별 프리셋 상이).

### 발주 서비스

| 서비스 | 비고 |
|---|---|
| [JLCPCB](https://jlcpcb.com/) | 해외(중국). 개인 개발자 사실상 표준 — 2층 5장 $2~ 수준, 한국 배송 1~2주. KiCad 거버 그대로 접수 |
| [PCBWay](https://www.pcbway.com/) | 해외(중국). JLCPCB와 양대 산맥, 품질/옵션 다양 |
| [한샘디지텍](https://www.hsdgt.com/) | 국내. 소량 시제작 대표 업체 — 빠른 납기, 한국어 응대 (해외 대비 가격 높음) |
| [샘플PCB](https://www.samplepcb.co.kr/) | 국내. 온라인 견적/발주 플랫폼 |

## 보드 실장 부품

| 부품 | 규격 / 부품번호 | 필요 수량 (구매 단위) | 링크 |
|---|---|---|---|
| 컨트롤러 | nice!nano v2 호환 (SuperMini nRF52840) | 2 | [AliExpress](https://www.aliexpress.com/item/1005009026511947.html) |
| 컨트롤러 소켓 (암) | 2.54mm 라운드홀 female 헤더, 12P×4줄 (40P 바 재단) | 4줄 (10줄 팩) | [AliExpress](https://www.aliexpress.com/item/32896689725.html) |
| 컨트롤러 핀 (수) | 2.54mm 금도금 라운드 수핀, 24핀/보드 | 48핀 (40P×10줄 팩) | [AliExpress](https://www.aliexpress.com/item/32219458766.html) |
| 핫스왑 소켓 | Kailh CPG151101S11 (MX) | 42 (70개 팩) | [AliExpress](https://www.aliexpress.com/item/1005012011087592.html) |
| 다이오드 | 1N4148, DO-35 THT (SOD-123 겸용 풋프린트) | 44 (50개 팩) | [AliExpress](https://www.aliexpress.com/item/1005007970187200.html) |
| 배터리 커넥터 | JST S2B-PH-K-S (PH 2.0mm, THT 사이드) | 2 (10개 팩) | [AliExpress](https://www.aliexpress.com/item/1005007176267255.html) |
| 배터리 | LiPo 301230, 3.7V ~110mAh, PH2.0 플러그, 보호회로 포함 | 2 | [AliExpress](https://www.aliexpress.com/item/1005005348368664.html) |
| 전원 스위치 | MSK-12C02 7핀 SMD 슬라이드 (Alps SSSS811101 호환) | 2 (50개 팩) | [AliExpress](https://www.aliexpress.com/item/4000685483225.html) |
| 리셋 스위치 | C&K PTS636 SM43 LFS (THT 상면 누름) | 2 (최소 5개) | [LCSC C2689636](https://www.lcsc.com/product-detail/C2689636.html) — 알리 미취급 |
| 로터리 엔코더 (옵션) | EC11, 푸시버튼 포함, 샤프트 15mm 권장 | 0~2 (5개 팩) | [AliExpress](https://www.aliexpress.com/item/1005008708996963.html) |

## 스위치 / 키캡

| 부품 | 규격 | 필요 수량 | 링크 |
|---|---|---|---|
| 키 스위치 | MX 호환 (예: Gateron Milky Yellow Pro, 5핀) | 42 (45개 팩) | [AliExpress](https://www.aliexpress.com/item/1005009861228283.html) |
| 키캡 | 1u × 42 (XDA/DSA blank PBT, Corne류 세트) | 1세트 | [AliExpress](https://www.aliexpress.com/item/1005008944545863.html) |
| 엔코더 노브 (옵션) | 6mm D/널링 샤프트용, 외경 ≤19mm | 0~2 | EC11 구매 시 함께 검색 |

## 케이스 하드웨어

케이스 자체는 구매가 아니라 출력: `case/exports/{left,right}_{top,bottom}.stl`
(PETG/PLA, 페리미터 4+, 인필 40%+, 쉘은 플레이트면·리드는 바깥면을 베드에).

| 부품 | 규격 | 필요 수량 (구매 단위) | 링크 |
|---|---|---|---|
| 히트셋 인서트 | M2, OD 3.2 × L 4.0 (구매 시 이 치수 선택 필수) | 10 (키트) | [AliExpress](https://www.aliexpress.com/item/1005007830491580.html) |
| 케이스 나사 | M2×14 접시머리 (DIN 965, 90°) | 10 (100개 팩) | [AliExpress](https://www.aliexpress.com/item/32367579698.html) |
| 범폰 | Ø8 × 2mm 실리콘, 자체접착 | ~12 (팩) | [AliExpress](https://www.aliexpress.com/item/1005006455782191.html) |

## 기타

- USB-C **데이터** 케이블 1개 (펌웨어 플래싱/충전용, 충전전용 케이블 불가)
- 납땜 인두 + 인서트 압입 팁 (인서트 키트에 팁 포함 옵션 있음)

## 조립 시 주의

- **TRRS 커넥터는 없다.** 완전 무선(BLE) 스플릿이라 보드에 풋프린트
  자체가 없다 — 유선 스플릿 BOM을 참고해 사지 말 것.
- **LiPo 극성**: JST-PH 배터리의 +/− 배선은 표준화되어 있지 않다.
  연결 전 보드 실크의 +/− 표기와 대조하고, 반대면 커넥터에서 핀을
  빼서 바꿔 끼운다. 극성 반대로 꽂으면 컨트롤러가 죽는다.
- **리버서블 보드**: 같은 PCB 2장에서 오른쪽은 앞면(F, "R hand back
  side" 실크 기준), 왼쪽은 뒷면(B)에 부품을 실장한다. 하프당 실장면이
  다를 뿐 부품은 동일.
- 컨트롤러는 직납하지 않고 소켓 실장한다 (라운드홀 암 헤더를 PCB에,
  수핀을 나노에). 클론 보드에 동봉되는 사각핀 헤더는 라운드 소켓과
  마모 궁합이 나빠 쓰지 않는다.
