# Gradient Descent: Learning by Following the Slope

2026-11-02 | CET-6 | 54 minutes

Preview: 2 min | Reading: 9 min | Chunks: 8 min | Reasoning: 7 min | Listening: 13 min | Retelling: 7 min | Writing: 5 min | Check: 3 min

## Preview | 2 minutes

Before reading, predict whether a useful direction is enough to guarantee a useful change. Keep that prediction and check it after paragraph four.

## Reading | 9 minutes

Original teaching passage. The photograph scenario and numerical experiment are hypothetical; the calculations are reproducible.

Imagine that you are adjusting the brightness of a photograph. You can make a change, inspect the result, and decide what to try next. Now replace personal preference with a precise numerical score. A computer can follow a similar cycle, provided that the score tells it how its current choices should change. This hypothetical editing task offers a starting point for understanding gradient descent. The aim is not to make random changes until something looks better, but to use local information to guide each update.

Suppose our entire model has just one adjustable number, w, and its loss is L(w) = (w - 3)^2. The loss measures distance from a particular target in a deliberately simplified example. At w = 0, the loss is 9. At w = 1, it is 4. We can see the best answer immediately, but pretend that we are allowed to inspect only our current position and its derivative. This restriction turns an obvious answer into a useful demonstration of an iterative method.

The derivative is L'(w) = 2(w - 3). At our starting point it equals -6. A negative derivative means that a small increase in w will lower the loss. Gradient descent therefore subtracts a multiple of the derivative: w(next) = w(now) - eta * L'(w). With a learning rate eta = 0.1, the next value is 0.6, and the new loss is 5.76. The derivative provides a direction and a scale of change; the learning rate controls how strongly we respond to that signal.

There is an important trap here. A direction that helps locally does not justify every possible step. Keeping the same starting point but choosing eta = 1.2 moves w to 7.2. The loss becomes 17.64, which is worse than the original 9. Both updates follow the negative derivative, yet only the smaller update improves the result. In this example, choosing a step is a testable decision, not a guarantee supplied by the word downhill. Recomputing the loss allows us to check what actually happened.

In a model with many parameters, a gradient collects the partial derivatives. Under the usual Euclidean geometry, its negative points toward steepest local decrease when the gradient is nonzero. Repeating suitably chosen updates can be useful even when solving directly is difficult. However, neural-network training involves a more complicated loss surface than our single valley. A small gradient or a flat-looking training curve does not establish that the best possible solution has been found, and lower training loss alone does not establish performance on unfamiliar data.

When explaining this process in English, separate the objective, the signal, the action and the evidence. State what the loss measures. Explain how the derivative guides an update. Then calculate or observe the result before claiming improvement. Finally, name a limitation of the example. This structure is useful beyond machine learning: it keeps a plausible explanation from becoming an unsupported promise. A careful account of progress describes both the proposed direction and the checks that could show the proposal was mistaken.

## Eight reusable chunks | 8 minutes

Cover the definitions. Explain each expression in your own words, then use two expressions to describe a problem you know.

| Expression | English meaning and example |
| --- | --- |
| minimize a loss function | Seek parameter values that make an error measure smaller. The optimizer aims to minimize a loss function. |
| adjust parameters iteratively | Change adjustable values through repeated updates. We adjust the parameters iteratively rather than guess once. |
| compute the gradient | Calculate the vector of partial derivatives. We compute the gradient before choosing an update. |
| move in the opposite direction | Go against the direction of a given signal. The update moves in the opposite direction to the gradient. |
| take a small step | Make a limited change. We take a small step and then check the loss. |
| overshoot the minimum | Move past a low point because an update is too large. A large learning rate may overshoot the minimum. |
| converge toward a minimum | Approach a low point through successive updates. Suitable updates may converge toward a minimum. |
| get stuck in a local minimum | Reach a low point that need not be the best overall. An optimizer can get stuck in a local minimum. |

## Reading and reasoning | 7 minutes

- 1. Why must we define a loss before we can judge whether an update improves the model?

- 2. Compare eta = 0.1 with eta = 1.2. How do the calculations challenge the claim that the negative-gradient direction guarantees a lower loss?

- 3. What can a flattening training-loss curve suggest, and what does it fail to prove?

- 4. A model reaches a stationary point. Why does this not necessarily mean that it has found a global minimum?

Response space:

____________________________
____________________________

## Listening | 13 minutes

Material: 3Blue1Brown, Gradient descent, how neural networks learn. Open the linked author lesson and its video. Use 03:01-12:19 as today's listening window (9 minutes 18 seconds).

Timing: predict for 2 minutes; listen once for 9 minutes 18 seconds; use the remaining 1 minute 42 seconds to revisit a difficult moment with English captions. The total is exactly 13 minutes.

Access check: the author's lesson and written explanation were opened on 2026-11-02. The video was not independently played during this example build. The timestamp is retained from the supplied daily lesson; if your player differs, use the cost-function and gradient explanation as the content boundary.

- Predict: What does the cost measure, and which quantities can training change?

- Listen without captions: record the connection between cost, gradient and parameter updates in three short notes.

- Verify: compare one note with the English captions or the author's written explanation. Record what you corrected, rather than inventing a complete transcript.

## Retelling | 7 minutes

Prepare for 3 minutes, speak for 1-2 minutes, then check your recording during the remaining time. Distinguish the gradient's direction from the direction of the actual parameter update.

- The goal: A loss function tells us...

- The signal: The derivative or gradient describes...

- The update: At each iteration, we...

- The limitation: Although the direction is useful, a learning rate that is too...

## Writing | 5 minutes

Write 80-100 words: Why can taking smaller steps lead to better progress when training a model?

Give a claim, use a numerical or conceptual example, and acknowledge that excessively small steps may slow progress. Use at least three of today's chunks.

Response space:

____________________________
____________________________
____________________________
____________________________
____________________________

## Quick check | 3 minutes

Let L(w) = (w - 3)^2. Start at w = 0 and use eta = 0.1. Since L'(w) = 2(w - 3), what is the next value of w? Explain the update direction in one English sentence before opening the key.

- A. -0.6

- B. 0.6

- C. 3.0

## Short routes | alternatives, not additional homework

15-minute route: read for 6 minutes, practise three chunks for 3 minutes, answer question 2 for 3 minutes, then retell for 3 minutes.

5-minute restart: read paragraphs three and four for 3 minutes. Use the remaining 2 minutes to explain the difference between direction and step size. Missed daily packs do not need to be made up.

## Answer key | check after responding

Reasoning 1: A loss makes the objective explicit. Without an agreed measure, a parameter change cannot be evaluated as an improvement in that objective.

Reasoning 2: Starting at zero, eta = 0.1 gives w = 0.6 and loss 5.76; eta = 1.2 gives w = 7.2 and loss 17.64. The original loss is 9. Both updates follow the negative derivative, but the larger one increases the loss. Direction and distance must be considered together.

Reasoning 3: A curve that stabilizes may suggest limited further improvement at the current scale and settings. It does not prove global optimality or good performance on unseen data; the curve may also look flat because the learning rate is extremely small.

Reasoning 4: A stationary point has zero gradient. Depending on the objective, it may be a local minimum, a local maximum or a saddle point. Extra assumptions are needed to identify a global minimum.

Quick check: B. At w = 0, the derivative is -6. Thus w(next) = 0 - 0.1 * (-6) = 0.6. In this example the negative derivative points toward increasing w.

Listening: answers depend on your notes. In the author's explanation, the cost measures prediction error on training examples; the gradient describes local change with respect to parameters; updates move against that gradient. Your correction should be traceable to a caption or a passage you actually checked.

Output self-check: Did I name the objective? Did I explain the minus sign? Did I discuss step size? Did I distinguish observed improvement from a guarantee? These are practice criteria, not an official CET-6 score.

## Sources

- [Google Machine Learning Crash Course: Gradient descent](https://developers.google.com/machine-learning/crash-course/linear-regression/gradient-descent) (accessed 2026-11-02)

- [3Blue1Brown: Gradient descent, how neural networks learn (author lesson and video)](https://www.3blue1brown.com/lessons/gradient-descent/) (accessed 2026-11-02)
