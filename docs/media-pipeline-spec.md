# ?뚯꽦 ?뚯씠?꾨씪??紐낆꽭 (STT/TTS/Storage/Queue)

> 理쒖쥌 ?섏젙?? `2026-04-09`

---

## 1. 紐⑹쟻

諛곕떖 遺덈쭔 ?꾪솕 ?곷떞 ?먮쫫?먯꽌 ?뱀랬/?꾩궗/?뚯꽦 ?묐떟 愿???ㅼ젣 ?숈옉??紐낆꽭?⑸땲??

1. ?뱀랬 ?낅줈??2. ?ㅻ툕?앺듃 ???3. STT ???깅줉/泥섎━
4. ?꾩궗 ???5. TTS ?꾨━酉??앹꽦

---

## 2. 而댄룷?뚰듃

| 怨꾩링 | ?뚯씪 | ??븷 |
| --- | --- | --- |
| API | `backend/app/api/v1/endpoints/calls.py` | ?뱀랬 ?낅줈?? ?꾩궗 ??? TTS ?꾨━酉?|
| API | `backend/app/api/v1/endpoints/queue.py` | ??議고쉶/泥섎━ |
| Service | `backend/app/services/delivery_issue_service.py` | ?뚯씠?꾨씪???ㅼ??ㅽ듃?덉씠??|
| STT | `backend/app/clients/stt_client.py` | ?ㅻ뵒??-> ?띿뒪??|
| TTS | `backend/app/clients/tts_client.py` | ?띿뒪??-> ?ㅻ뵒??|
| Storage | `backend/app/clients/storage_client.py` | ?뚯씪 ???議고쉶 |
| Worker | `backend/app/workers/queue_worker.py` | ??諛곗튂 ?ㅽ뻾 |

---

## 3. STT

### 3.1 Provider

- `mock`: 怨좎젙 ?섑뵆 ?꾩궗 諛섑솚
- `openai`: OpenAI ?꾩궗 API ?몄텧
- 湲고?: placeholder ?띿뒪??
### 3.2 ???곗꽑?쒖쐞

1. `STT_PROVIDER_API_KEY`
2. `OPENAI_API_KEY`

### 3.3 異쒕젰 speaker ?뺢퇋??
- `student`, `customer`, `user` -> `customer`
- `mentor`, `agent`, `ai` -> `ai`
- `counselor` -> `counselor`

---

## 4. TTS

### 4.1 Provider

- `mock`: preview 諛붿씠???앹꽦
- `openai`: OpenAI speech API ?몄텧

### 4.2 ???곗꽑?쒖쐞

1. `TTS_PROVIDER_API_KEY`
2. `OPENAI_API_KEY`

---

## 5. ??μ냼

### 5.1 濡쒖뺄 ?????
- ?뱀랬: `recordings/{lead_id}/{call_id}/{uuid}{ext}`
- TTS ?꾨━酉? `tts-previews/{uuid}.mp3`

### 5.2 Provider

- `local`: 濡쒖뺄 ?붾젆?곕━ ???- `s3`: S3 ?먮뒗 ?명솚 ?ㅽ넗由ъ?

---

## 6. ??泥섎━

### 6.1 ?앹꽦

`POST /calls/recordings/upload` ??

1. ?뚯씪 ???2. `recordings` 硫뷀??곗씠?????3. `async_tasks`??`stt_transcription` ?깅줉 (`queued`)

### 6.2 ?ъ떆???뺤콉

- `attempts + 1 < QUEUE_MAX_ATTEMPTS` ?대㈃ `queued`濡??щ같移?- ?쒕룄 珥덇낵 ??`failed`

### 6.3 ?뚯빱

- `POST /queue/workers/run`
- `queued` ?묒뾽???앹꽦 ?쒖꽌?濡?泥섎━

---

## 7. ?댁쁺 沅뚯옣媛?
| ?섍꼍 | STT | TTS | Storage | Queue |
| --- | --- | --- | --- | --- |
| 濡쒖뺄 | `mock` | `mock` | `local` | `QUEUE_AUTO_PROCESS=true` |
| ?ㅽ뀒?댁쭠 | `openai` | `openai` | `s3`/?명솚 | ?ㅼ?以꾨윭 湲곕컲 |
| ?댁쁺 | ?곸슜/`openai` | ?곸슜/`openai` | `s3` | ?몃? ?뚯빱 ?곸떆 |


