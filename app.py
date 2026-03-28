import re
import streamlit as st


def fix_furigana(text: str) -> str:
    INVALID_START = frozenset('っんぁぃぅぇぉゃゅょ')

    NOT_FURIGANA_SUBSTR = (
        'を',
        'っこ', 'って', 'っち',
        'ていた', 'ている', 'ており', 'てい',
        'であ', 'だと', 'だっ', 'だか',
        'はそ', 'はな',
        'されぬ', 'されて', 'された', 'させた', 'させて',
        'からず', 'ならず', 'わせた',
    )

    CONNECTOR_STARTS = (
        'として', 'となり', 'となる', 'となっ',
        'によって', 'によると', 'にあたり', 'にあって',
        'にとって', 'にわたり', 'にわたっ', 'において',
        'に対して', 'においては', 'については',
        'にされ', 'にさせ', 'される', 'された', 'させる', 'させて',
        'してい', 'してお', 'している', 'していた',
        'だった', 'だろう', 'だから', 'だけど', 'だとい',
        'をきっかけ', 'をもとに', 'をつうじ',
        'ながら', 'なった', 'になっ', 'になり',
        'のため', 'のよう', 'たため', 'たから',
        'などの', 'などに', 'などで', 'などを',
        'ことが', 'ことに', 'ことも', 'ことを',
        'ために',
    )

    def replace(m: re.Match) -> str:
        leading, reading, trailing = m.group(1), m.group(2), m.group(3)
        if reading[0] in INVALID_START:
            return m.group(0)
        if any(reading.startswith(c) for c in CONNECTOR_STARTS):
            return m.group(0)
        if any(s in reading for s in NOT_FURIGANA_SUBSTR):
            return m.group(0)
        return f'{leading}{trailing}（{reading}）'

    text = re.sub(r'([一-龯々])([ぁ-ん]{4,})([一-龯々]+)', replace, text)
    return text


def clean_text(text: str, with_furigana: bool = False) -> str:
    if with_furigana:
        text = fix_furigana(text)

    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'(?<!\n)(?=[▼■●◆◎※▲◇【])', '\n', text)
    text = re.sub(r'\](?=[^\s\n])', ']\n', text)

    heading_end = r'について|とは|一覧|まとめ|クリア条件|勝利条件|終了条件'
    text = re.sub(
        r'([▼■●◆◎※▲◇][^\n。！？]*?(?:' + heading_end + r'))(\S)',
        r'\1\n\2',
        text
    )

    paragraphs = text.split('\n\n')
    cleaned = []
    for para in paragraphs:
        lines = para.splitlines()
        merged_lines = []
        buffer = ''
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if buffer:
                if re.search(r'[。！？…」』】）\]\.\!\?]$', buffer):
                    merged_lines.append(buffer)
                    buffer = line
                elif re.match(r'^[▼■●◆◎※▲◇]', buffer) or re.match(r'^[▼■●◆◎※▲◇]', line):
                    merged_lines.append(buffer)
                    buffer = line
                elif re.match(r'^[「『【（\(]', line):
                    merged_lines.append(buffer)
                    buffer = line
                else:
                    buffer += line
            else:
                buffer = line
        if buffer:
            merged_lines.append(buffer)
        cleaned.append('\n'.join(merged_lines))

    result = '\n\n'.join(cleaned)

    JP = r'[\u3000-\u9fff\uff00-\uffef]'
    result = re.sub(r'(?<=' + JP + r') +(?=' + JP + r')', '', result)
    result = re.sub(r'(?<=' + JP + r') +(?=[A-Za-z0-9])', '', result)
    result = re.sub(r'(?<=[A-Za-z0-9]) +(?=' + JP + r')', '', result)
    result = re.sub(r'([「『【]) ', r'\1', result)
    result = re.sub(r' ([」』】])', r'\1', result)

    return result


# --- UI ---
st.set_page_config(page_title='TRPG テキスト整形ツール', layout='wide')
st.title('TRPG テキスト整形ツール')
st.caption('PDFからコピーしたシナリオテキストの改行・スペース・ルビを整形します')

with_furigana = st.checkbox('ルビも整形する（誤変換の可能性あり）', value=False)

col1, col2 = st.columns(2)

with col1:
    st.subheader('貼り付け（整形前）')
    input_text = st.text_area('', height=500, placeholder='ここにテキストを貼り付けてください', label_visibility='collapsed')

with col2:
    st.subheader('コピー用（整形後）')
    if input_text.strip():
        result = clean_text(input_text, with_furigana=with_furigana)
        st.text_area('', value=result, height=500, label_visibility='collapsed')
        before, after = len(input_text), len(result)
        label = '整形完了（ルビあり）' if with_furigana else '整形完了'
        st.caption(f'{label}　{before} 文字 → {after} 文字' + ('　※誤変換がある場合は手動で修正してください' if with_furigana else ''))
    else:
        st.text_area('', value='', height=500, placeholder='左にテキストを入力すると自動で整形されます', label_visibility='collapsed')
