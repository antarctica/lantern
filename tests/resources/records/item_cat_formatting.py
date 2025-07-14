from lantern.lib.metadata_library.models.record.enums import HierarchyLevelCode
from tests.resources.records.utils import make_record

# A record for an ItemCatalogue instance with examples of Markdown formatting in all supported fields.

abstract = """
Pargraph: I spent so much time making sweet jam in the kitchen that it's hard to hear anything over the clatter of the
tin bath. I shall hide behind the couch.

Another paragraph: Interfere? Michael: I'm sorry, have we met? She calls it a mayonegg. The only thing more terrifying than the
escaped lunatic's hook was his twisted call…

Headings:

# Heading 1
...

## Heading 2
...

### Heading 3
...

#### Heading 4
...

##### Heading 5
...

###### Heading 6
...

Link: [Some link](#).

Auto-link: https://www.example.com.

Auto mailto: conwat@example.com.

Bold: No, I was ashamed to be **SEEN** with you. I like being **WITH** you.

Italics: _(Guy's a pro.)_

Keyboard shortcut: <kbd>Cmd</kbd>+<kbd>v</kbd>

Inline code: `print("Hello Rencia.")`

Blockquote:
> Heyyyyy campers!

Unordered list (with a two new lines between this paragraph and the start of the list):

* Say something that will terrify me.
* Lindsay: Kiss me.
* Tobias: No, that didn't do it.

Unordered list (with a single new line between this paragraph and the start of the list):
* Say something that will terrify me.
* Lindsay: Kiss me.
* Tobias: No, that didn't do it.

Ordered list:

1. Chickens don't clap!
2. Am I in two thirds of a hospital room?

Code block:

```
def print_hello():
print("Hello Rencia.")
```

Preformatted:

<pre>
lines = [
"Probably out there without a flipper, swimming around in a circle, freaking out his whole family.",
"We'll have to find something to do so that people can look at you without wanting to kill themselves.",
"I'm gonna build me an airport, put my name on it. Why, Michael? So you can fly away from your feelings?",
]
</pre>

Table:

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Row 1    | Row 1    | Row 1    |
| Row 2    | Row 2    | Row 2    |

Horizontal rule:

I didn't get into this business to please sophomore Tracy Schwartzman, so… onward and upward. On… Why, Tracy?! Why?!!
---
You're a good guy, mon frere. That means brother in French.

Markdown Image:

![I don't know how I know that. I took four years of Spanish.](https://images.unsplash.com/photo-1494216928456-ae75fd96603d?q=80&w=1080&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D)

HTML figure with caption:

<figure>
<img src="https://images.unsplash.com/photo-1465060780892-48505fc8f941?q=80&w=1080&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D" alt="marmite" />
<figcaption>We need a name. Maybe 'Operation Hot Mother'.</figcaption>
</figure>
"""
purpose = """
I shall hide behind the couch. _(Guy's a pro.)_

* Say something that will terrify me with [a link](#).

No, I was ashamed to be **SEEN** with you. I like being **WITH** you!

1. Chickens don't clap!
"""
other_citation_details = """
I shall hide behind the couch. _(Guy's a pro.)_

* Say something that will terrify me with [a link](#).

No, I was ashamed to be **SEEN** with you. I like being **WITH** you!

1. Chickens don't clap!
"""
record = make_record(
    file_identifier="e0df252c-fb8b-49ff-9711-f91831b66ea2",
    hierarchy_level=HierarchyLevelCode.PRODUCT,
    title="Test Resource - Product to test **Markdown** _formatting_",
    abstract=abstract,
    purpose="Item to test all supported Product properties are recognised and presented correctly.",
)
record.identification.other_citation_details = other_citation_details
