# About
Unofficial but usefull functionality, developed by the community, to make GroundX more convenient and more powerfull. Use in your projects, or take inspiration in your own codebase.

# Installation

To install the most recent version:
```
pip install git+https://github.com/EyeLevel-ai/groundx_community.git
```

To install from a specific commit hash:
```
pip install git+https://github.com/EyeLevel-ai/groundx_community.git@<commit-hash>
```

# Chat Utils

## In-Text Citation
`generate_cited_response` is an augmentation and generation tool designed to generate in-text citations within a RAG system.

```
from groundx_community.chat_utils.citing import generate_cited_response
```


The major input to the `generate_cited_response` function is chunks, which consists of three fields:
1. `text`, which is passed to the LLM
1. `uuid` associated with each chunk, used to reference the in-text citation
1. `render_name`, used to render the in-text citation
1. `source_data`, which is an optional set of keys and values that will be injected into the final output upon generation of the in-text citation.

properly configured chunks have the following general structure:
```
chunks=[
        {
            "text": "text the LLM should use"
            "uuid": "11111111-aaaa-bbbb-cccc-000000000001",
            "render_name": "example.txt",
            "source_data": {
                "key1": "value1".
                "key2": "value2"
            }
        },
        ...
    ]
```

There are also two additional arguments for generating the in-text citation:
1. `system_prompt`, which functions as a system prompt defining application level guidance. Note, additional prompting is done to guide the model to use in-text citations. This prompt should guide the model in terms of application logic, not logic around in-text citations.
1. `query`, the query which the model should answer, based on the chunks

In-text citation defaults to using `GPT-4o`, and expects an `OPENAI_API_KEY` to be defined as an environment variable. If you wish to use OpenAI with GPT-4o, the following code will suffice:

```
# Use default GPT-4o
response = await generate_cited_response(
    chunks=my_chunks,
    system_prompt="You are a helpful assistant.",
    query="What is the verdict?",
)
```

If you want to specify another model as the completion model, the `generate_cited_response` function accepts any langchain chat model that inherits from `langchain_core.language_models.chat_models.BaseChatModel`. For instance, here's an example of using Claude 3 haiku.

```
# Use a custom Claude model
from langchain_anthropic import ChatAnthropic

custom_llm = ChatAnthropic(model="claude-3-haiku-20240307", api_key="your-anthropic-key")

response = await generate_cited_response(
    chunks=my_chunks,
    system_prompt="You are a helpful assistant.",
    query="What is the verdict?",
    llm=custom_llm,
)
```

The end result is a string with the following in-text citations injected:
```
This is a response that needs to be cited<InTextCitation chunkId="11111111-aaaa-bbbb-cccc-000000000001" renderName="example.txt" key1="value1" key2="value2"></InTextCitation>
```

`InTextCitation` can be configured as necessary to allow for arbitrary functionality. For example, in [this example](https://github.com/EyeLevel-ai/groundx_community/blob/main/examples/rag_in_text_citation.ipynb), you can see an example of turning in-text citations into clickable links which open the respective PDF being referenced.

## Upload Polling

Handy little util that polls an upload, printing out statuses, then exits when done. Allows one to halt a process until an upload is completed. It has one required argument, which is the `process_id` being polled.

it has two verbosity settings:
- `print_updates`: Prints update of current state
- `print_completed`: Once the upload process is complete, print a notification

Upload processes can have the following states:
```
queued, processing, error, complete, cancelled, active, inactive
```

This function polls upload processes which are still in progress (`queue`, `processing`, `active`) then stops when the upload process completes (`error`, `complete`, `cancelled`, `inactive`). The final process state is returned, as a string, as the ultimate output of the function.

Usage looks like this:
```
from groundx_community.upload_utils.management import upload_poller

final_state = upload_poller(
        client=client,
        process_id=process_id,
        poll_interval=2.0,
        timeout=300,
        logger=logger,
        print_completed=True,
    )
```

Currently this function only supports polling one process, though one can trivially iterate over a list of upload processes to wait for them to complete, or parallelized for more clever management of multiple upload processes.

# Testing

to test, `tests` should have a properly configured .env variable (as outlined in `template_env.txt`). Then run this

```uv run -m pytest tests/```

it should run tests against the library as it's defined in `src`
