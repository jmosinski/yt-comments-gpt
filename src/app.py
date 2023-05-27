import streamlit as st
import openai
from youtube_comment_downloader import YoutubeCommentDownloader


def fetch_comments(url, max_tokens=2500):
    downloader = YoutubeCommentDownloader()
    comments = []
    num_tokens = 0
    for data in downloader.get_comments_from_url(url, sort_by=0):
        if data['reply']:
            continue
        comment = ' '.join(data['text'].split())
        num_tokens += len(comment) / 3.3  # One token is approx. 4 chars in English
        if num_tokens > max_tokens:
            break
        comments.append(comment)
    return comments


def drop_comments(comments, max_tokens, requested_tokens):
    num_comments_to_drop = int((1 - 0.7 * max_tokens / requested_tokens) * len(comments) + 1)
    return comments[:-num_comments_to_drop]


def get_markdown_report(comments, max_tokens=1000):
    joined_comments = '\n'.join(comments)
    num_comments = len(comments)
    prompt = f"""
Create a detailed, polite and constructive report answering the provided questions based on the provided comments, use markdown format. The questions are enclosed with <questions start><questions end>.  Additional instructions for answering a given question are enclosed with <>. Rephrase the qustions approprietly for the report format. The comments are enclosed with <comments start><comments end> and separeted by new lines. There are {num_comments} most popular comments. 

<questions start>
What percentage of comments have "Positive", "Negative", "Neutral" sentiment? <to answer follow steps: 1. classify each comment as positive, negative, netural 2. compute the average scores 3. return results as percentages by dividing the avera by the total number of comments, use bulletpoint format>
What people liked? <bullet list format, do not cite comments, provide details>
What people disliked?  <bullet list format. do not cite comments, provide details>
What people suggest to improve and how? <bullet list format, do not cite comments, provide details>
What is the overall opinion of the video? <plain text format, do not list answers to previous questions>
<questions end>

<comments start>
{joined_comments}
<comments end>
"""
    markdown_report = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=max_tokens,
        top_p=1,
    ).choices[0].message["content"]
    return markdown_report


def main():
    max_tokens = 4000
    prompt_tokens = 300
    max_response_tokens = 1000
    max_tokens_comments = max_tokens - prompt_tokens - max_response_tokens

    st.title("YouTube Comments Analyzer")
    url = st.text_input("Enter YouTube URL")
    api_key = st.text_input("Enter OpenAI API Key")
    if st.button("Analyze Comments"):
        openai.api_key = api_key
        try:
            comments = fetch_comments(url=url, max_tokens=max_tokens_comments)
            try:
                markdown_report = get_markdown_report(comments=comments)
            except Exception as e:
                print(e)
                import re
                requested_tokens = int(max(re.findall(r'\d+\.?\d*', str(e))))
                requested_comments_tokens = requested_tokens - max_response_tokens - prompt_tokens
                reduced_comments = drop_comments(
                    comments, max_tokens=max_tokens_comments, requested_tokens=requested_comments_tokens
                )
                markdown_report = get_markdown_report(comments=reduced_comments, max_tokens=max_response_tokens)
            st.markdown(markdown_report)
        except Exception as e:
            print(e)
            st.error("Something went wrong! Probably wrong URL or API Key. Please check your inputs and try again.")


if __name__ == '__main__':
    main()

