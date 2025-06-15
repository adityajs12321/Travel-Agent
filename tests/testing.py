import lmstudio as lms

model = lms.llm("qwen3-8b-mlx", config={
    "contextLength": 2048,
})

model.model = "qwen3-8b-mlx"

print(model.respond("hello how are you /no_think").content)